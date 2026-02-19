"""
Risk-level scoring from EAR, MAR, and head pose.
Defines risk levels and triggers audio/visual alerts.
"""
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from app.models import RiskEventPayload, RiskLevel, RiskType
from app.vision.landmarks import FrameMetrics

logger = logging.getLogger(__name__)


@dataclass
class RiskEngineConfig:
    ear_threshold: float = 0.2
    ear_closure_seconds: float = 0.5
    mar_threshold: float = 0.16  # above this = yawn (tune from dashboard: closed ~0.14, open ~0.18)
    mar_sustained_seconds: float = 0.3  # MAR must stay above threshold this long to count as yawn
    head_pose_tilt_threshold_deg: float = 25.0
    # Cooldown between same-type events (seconds)
    event_cooldown_sec: float = 2.0


class RiskEngine:
    """
    Scores current frame metrics and produces risk events.
    Tracks prolonged eye closure (time window) and triggers alerts.
    """

    def __init__(self, config: RiskEngineConfig):
        self.config = config
        self._eye_closed_since: Optional[float] = None
        self._mar_above_since: Optional[float] = None  # when MAR first went above threshold
        self._last_event_time: dict[str, float] = {}
        self._on_risk_event: Optional[Callable[[RiskEventPayload], None]] = None
        self._session_id: Optional[str] = None

    def set_session_id(self, session_id: Optional[str]):
        self._session_id = session_id

    def set_callback(self, callback: Callable[[RiskEventPayload], None]):
        self._on_risk_event = callback

    def _should_fire(self, event_type: str) -> bool:
        now = time.time()
        last = self._last_event_time.get(event_type, 0)
        if now - last < self.config.event_cooldown_sec:
            return False
        self._last_event_time[event_type] = now
        return True

    def _emit(self, payload: RiskEventPayload):
        if self._on_risk_event:
            try:
                self._on_risk_event(payload)
            except Exception as e:
                logger.exception("Risk event callback error: %s", e)

    def evaluate(self, metrics: FrameMetrics, frame_timestamp: Optional[datetime] = None) -> Optional[RiskEventPayload]:
        """
        Evaluate metrics and return a RiskEventPayload if a risk event occurred.
        Also tracks prolonged blink (eye closure over time window).
        """
        if not metrics.face_detected:
            self._eye_closed_since = None
            self._mar_above_since = None
            return None

        now = time.time()
        ts = frame_timestamp or datetime.utcnow()
        level = RiskLevel.LOW
        event_type: Optional[RiskType] = None
        metrics_dict = metrics.to_dict()

        # --- Eye closure (EAR) ---
        if metrics.ear is not None:
            if metrics.ear < self.config.ear_threshold:
                if self._eye_closed_since is None:
                    self._eye_closed_since = now
                else:
                    closed_duration = now - self._eye_closed_since
                    if closed_duration >= self.config.ear_closure_seconds:
                        if self._should_fire("EYE_CLOSURE"):
                            if closed_duration >= 2.0:
                                level = RiskLevel.CRITICAL
                            elif closed_duration >= 1.0:
                                level = RiskLevel.HIGH
                            else:
                                level = RiskLevel.MEDIUM
                            event_type = RiskType.EYE_CLOSURE
                            metrics_dict["ear_closure_seconds"] = round(closed_duration, 2)
            else:
                self._eye_closed_since = None

        # --- Yawn (MAR): require sustained open mouth to avoid false positives (talking, smile) ---
        if metrics.mar is not None:
            if metrics.mar >= self.config.mar_threshold:
                if self._mar_above_since is None:
                    self._mar_above_since = now
                else:
                    open_duration = now - self._mar_above_since
                    if open_duration >= self.config.mar_sustained_seconds and self._should_fire("YAWN"):
                        event_type = RiskType.YAWN
                        if metrics.mar >= 0.20:
                            level = RiskLevel.HIGH
                        else:
                            level = RiskLevel.MEDIUM
                        metrics_dict["mar_sustained_seconds"] = round(open_duration, 2)
            else:
                self._mar_above_since = None

        # --- Head pose ---
        if metrics.head_pose:
            tilt = abs(metrics.head_pose.get("tilt_deg", 0))
            if tilt >= self.config.head_pose_tilt_threshold_deg:
                if self._should_fire("HEAD_POSE"):
                    event_type = RiskType.HEAD_POSE
                    if tilt >= 40:
                        level = RiskLevel.HIGH
                    else:
                        level = RiskLevel.MEDIUM
                    metrics_dict["head_tilt_deg"] = round(tilt, 1)

        if event_type is None:
            return None

        payload = RiskEventPayload(
            level=level,
            type=event_type,
            timestamp=ts,
            session_id=self._session_id,
            metrics=metrics_dict,
        )
        self._emit(payload)
        beep_alert(level)
        return payload


def beep_alert(level: RiskLevel):
    """Simple audio alert: print BEL character or use system beep."""
    try:
        # BEL character can trigger terminal beep on some systems
        sys.stdout.write("\a")
        sys.stdout.flush()
    except Exception:
        pass
