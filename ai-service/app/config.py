"""Configuration from environment variables."""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Config:
    """AI service configuration."""

    port: int
    backend_url: Optional[str]
    # Video source: 0 for default camera, or URL (e.g. rtsp://, http://, or file path)
    video_source: str
    # EAR threshold below which eye is considered closed
    ear_threshold: float
    # Seconds of eye closure to count as prolonged blink
    ear_closure_seconds: float
    # MAR threshold above which mouth is considered yawning
    mar_threshold: float
    # MAR must stay above threshold this long (seconds) to count as yawn (reduces false positives)
    mar_sustained_seconds: float
    # Head pose deviation (degrees) to consider risk
    head_pose_tilt_threshold_deg: float
    # Retry when sending events to backend
    backend_retry_max: int
    backend_retry_backoff_sec: float

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            port=int(os.environ.get("PORT", "8000")),
            backend_url=os.environ.get("BACKEND_URL") or None,
            video_source=os.environ.get("VIDEO_SOURCE", "0"),
            ear_threshold=float(os.environ.get("EAR_THRESHOLD", "0.2")),
            ear_closure_seconds=float(os.environ.get("EAR_CLOSURE_SECONDS", "0.5")),
            mar_threshold=float(os.environ.get("MAR_THRESHOLD", "0.16")),
            mar_sustained_seconds=float(
                os.environ.get("MAR_SUSTAINED_SECONDS", "0.4")
            ),
            head_pose_tilt_threshold_deg=float(
                os.environ.get("HEAD_POSE_TILT_THRESHOLD_DEG", "25.0")
            ),
            backend_retry_max=int(os.environ.get("BACKEND_RETRY_MAX", "5")),
            backend_retry_backoff_sec=float(
                os.environ.get("BACKEND_RETRY_BACKOFF_SEC", "1.0")
            ),
        )
