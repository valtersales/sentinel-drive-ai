"""
Sentinel Drive AI - Python microservice.
Computer vision (MediaPipe), risk engine, and backend event forwarding.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from app.backend_client import BackendClient
from app.config import Config
from app.models import RiskEventPayload, RiskLevel, RiskType
from app.pipeline import get_last_frame_jpeg, get_state, start_pipeline, stop_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = Config.from_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cleanup on shutdown."""
    yield
    stop_pipeline()


app = FastAPI(
    title="Sentinel Drive AI",
    version="0.2.0",
    description="""
AI microservice for driver drowsiness detection.

- **Computer vision:** MediaPipe Face Mesh, EAR (eye aspect ratio), MAR (mouth aspect ratio), head pose.
- **Risk engine:** Risk levels (LOW, MEDIUM, HIGH, CRITICAL) and event types (EYE_CLOSURE, YAWN, HEAD_POSE).
- **Event contract:** Risk events are sent to the backend via `POST /api/v1/risk-events` with the payload schema below.
    """,
    lifespan=lifespan,
)


_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/dashboard", response_class=FileResponse)
def dashboard():
    """Live dashboard: webcam stream + metrics and alerts. Start the pipeline first."""
    dashboard_html = _STATIC_DIR / "dashboard.html"
    if not dashboard_html.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(dashboard_html, media_type="text/html")


@app.get("/", response_class=FileResponse)
def root():
    """Redirect root to dashboard."""
    return dashboard()


@app.get("/health")
def health():
    """Health check for Docker and orchestration."""
    return {"status": "UP", "service": "sentinel-drive-ai"}


@app.get("/api/v1/metrics")
def get_metrics():
    """Return last frame metrics from the running pipeline (if any). Includes error if pipeline failed (e.g. webcam not open)."""
    state = get_state()
    out = {
        "metrics": state.last_metrics.to_dict() if state.last_metrics else None,
        "frame_count": state.frame_count,
        "pipeline_running": state.running,
        "last_alert": state.last_alert_text,
        "last_alert_at": state.last_alert_at,
    }
    if state.error:
        out["error"] = state.error
    return out


MJPEG_BOUNDARY = b"frame"


async def _mjpeg_stream():
    """Yield MJPEG parts (multipart/x-mixed-replace)."""
    while True:
        jpeg = get_last_frame_jpeg()
        if jpeg:
            yield (
                b"--" + MJPEG_BOUNDARY + b"\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n"
            ) + jpeg + b"\r\n"
        await asyncio.sleep(1 / 15)


@app.get("/api/v1/stream")
async def stream_mjpeg():
    """
    Live MJPEG stream of the pipeline output (webcam + overlay with EAR, MAR, alert).
    Pipeline must be started first (GET/POST /api/v1/pipeline/start).
    """
    state = get_state()
    if not state.running:
        raise HTTPException(
            status_code=503,
            detail="Pipeline not running. Start it with GET or POST /api/v1/pipeline/start",
        )
    # Wait for first frame so we don't send 200 with empty body
    for _ in range(100):
        if get_last_frame_jpeg():
            break
        await asyncio.sleep(0.1)
    else:
        raise HTTPException(
            status_code=503,
            detail="No frame from pipeline yet (camera may be starting). Retry in a few seconds.",
        )
    return StreamingResponse(
        _mjpeg_stream(),
        media_type=f"multipart/x-mixed-replace; boundary={MJPEG_BOUNDARY.decode()}",
    )


def _pipeline_start():
    """Start the video pipeline in the background (uses VIDEO_SOURCE, e.g. 0 for webcam)."""
    if start_pipeline(config):
        return {"status": "started", "message": "Video pipeline started. Use GET /api/v1/metrics to see live data."}
    return {"status": "already_running", "message": "Pipeline is already running."}


@app.post("/api/v1/pipeline/start")
def pipeline_start_post():
    return _pipeline_start()


@app.get("/api/v1/pipeline/start")
def pipeline_start_get():
    """Start the pipeline (GET allowed so opening in browser works)."""
    return _pipeline_start()


def _pipeline_stop():
    stop_pipeline()
    return {"status": "stopped"}


@app.post("/api/v1/pipeline/stop")
def pipeline_stop_post():
    return _pipeline_stop()


@app.get("/api/v1/pipeline/stop")
def pipeline_stop_get():
    """Stop the pipeline (GET allowed for convenience)."""
    return _pipeline_stop()


@app.post("/api/v1/events", response_model=dict)
def send_event_to_backend(payload: RiskEventPayload):
    """
    Accept a risk event and forward it to the backend (if BACKEND_URL is set).
    Use this to test the event contract or to inject events.

    **Event contract (required fields for backend ingestion):**
    - `level`: LOW | MEDIUM | HIGH | CRITICAL
    - `type`: EYE_CLOSURE | YAWN | HEAD_POSE | COMBINED
    - `timestamp`: ISO 8601 (UTC)
    - `session_id`: optional
    - `metrics`: object (e.g. ear, mar, head_pose)
    """
    if not config.backend_url:
        raise HTTPException(
            status_code=503,
            detail="BACKEND_URL not configured; cannot forward events",
        )
    client = BackendClient(
        config.backend_url,
        max_retries=config.backend_retry_max,
        backoff_sec=config.backend_retry_backoff_sec,
    )
    try:
        ok = client.send_event(payload)
        if not ok:
            raise HTTPException(status_code=502, detail="Backend did not accept the event")
        return {"status": "sent", "event_type": payload.type, "level": payload.level}
    finally:
        client.close()


@app.get("/api/v1/event-contract")
def event_contract():
    """Return the risk event payload schema for backend integration."""
    return {
        "description": "Payload for POST /api/v1/risk-events (backend ingestion)",
        "required_fields": ["level", "type", "timestamp"],
        "optional_fields": ["session_id", "metrics", "message"],
        "level_enum": [e.value for e in RiskLevel],
        "type_enum": [e.value for e in RiskType],
        "example": {
            "level": "MEDIUM",
            "type": "YAWN",
            "timestamp": "2025-02-18T12:00:00Z",
            "session_id": "session-123",
            "metrics": {"mar": 0.62, "ear": 0.28},
        },
    }
