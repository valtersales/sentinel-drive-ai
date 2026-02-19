"""
Video pipeline: capture -> face processor -> risk engine -> backend + alerts.
Runs in a background thread when VIDEO_SOURCE is set.
"""
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import cv2

from app.backend_client import BackendClient
from app.config import Config
from app.risk_engine import RiskEngine, RiskEngineConfig
from app.vision.capture import frame_generator, open_video_source
from app.vision.face_processor import FaceProcessor, draw_overlay
from app.vision.landmarks import FrameMetrics

logger = logging.getLogger(__name__)


@dataclass
class PipelineState:
    running: bool = False
    last_metrics: Optional[FrameMetrics] = None
    last_alert_text: Optional[str] = None
    last_alert_at: Optional[float] = None  # time.time() when last alert was set (for "ok" state after cooldown)
    last_event: Optional[dict] = None
    frame_count: int = 0
    error: Optional[str] = None
    last_frame_jpeg: Optional[bytes] = None  # latest frame with overlay, for MJPEG stream


_state = PipelineState()
_lock = threading.Lock()


def get_state() -> PipelineState:
    with _lock:
        return PipelineState(
            running=_state.running,
            last_metrics=_state.last_metrics,
            last_alert_text=_state.last_alert_text,
            last_alert_at=_state.last_alert_at,
            last_event=_state.last_event,
            frame_count=_state.frame_count,
            error=_state.error,
            last_frame_jpeg=_state.last_frame_jpeg,
        )


def get_last_frame_jpeg() -> Optional[bytes]:
    """Return the latest frame as JPEG bytes (with overlay), for MJPEG stream. Thread-safe."""
    with _lock:
        return _state.last_frame_jpeg


def _run_pipeline(config: Config):
    global _state
    source = config.video_source
    cap = open_video_source(source)
    if cap is None:
        with _lock:
            _state.running = False
            _state.error = f"Could not open video source: {source}"
        return

    processor = FaceProcessor()
    risk_config = RiskEngineConfig(
        ear_threshold=config.ear_threshold,
        ear_closure_seconds=config.ear_closure_seconds,
        mar_threshold=config.mar_threshold,
        mar_sustained_seconds=config.mar_sustained_seconds,
        head_pose_tilt_threshold_deg=config.head_pose_tilt_threshold_deg,
    )
    engine = RiskEngine(risk_config)
    backend_client: Optional[BackendClient] = None
    if config.backend_url:
        backend_client = BackendClient(
            config.backend_url,
            max_retries=config.backend_retry_max,
            backoff_sec=config.backend_retry_backoff_sec,
        )
        engine.set_callback(lambda p: backend_client.send_event(p))

    try:
        with _lock:
            _state.running = True
            _state.error = None
        for frame, idx in frame_generator(source):
            with _lock:
                if not _state.running:
                    break
            if frame is None:
                break
            metrics = processor.process_frame(frame)
            with _lock:
                _state.last_metrics = metrics
                _state.frame_count = idx + 1
            event = engine.evaluate(metrics, datetime.utcnow())
            if event:
                with _lock:
                    _state.last_event = event.model_dump(mode="json")
                    _state.last_alert_text = f"{event.level.value}: {event.type.value}"
                    _state.last_alert_at = time.time()
            with _lock:
                now = time.time()
                if _state.last_alert_at is not None and (now - _state.last_alert_at) <= 5:
                    status_text = _state.last_alert_text or "—"
                    status_ok = False
                else:
                    status_text = "It's all good"
                    status_ok = True
            overlay_frame = draw_overlay(frame, metrics, status_text=status_text, status_ok=status_ok)
            ok, jpeg_bytes = cv2.imencode(".jpg", overlay_frame)
            if ok and jpeg_bytes is not None:
                with _lock:
                    _state.last_frame_jpeg = jpeg_bytes.tobytes()
    except Exception as e:
        logger.exception("Pipeline error: %s", e)
        with _lock:
            _state.error = str(e)
    finally:
        processor.close()
        if backend_client:
            backend_client.close()
        with _lock:
            _state.running = False


_thread: Optional[threading.Thread] = None


def start_pipeline(config: Config) -> bool:
    """Start pipeline in background if not already running."""
    global _thread
    with _lock:
        if _state.running:
            return False
    _thread = threading.Thread(target=_run_pipeline, args=(config,), daemon=True)
    _thread.start()
    return True


def stop_pipeline():
    """Signal pipeline to stop."""
    with _lock:
        _state.running = False
