"""Risk event and API data models."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_serializer


class RiskLevel(str, Enum):
    """Risk severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskType(str, Enum):
    """Type of risk event."""

    EYE_CLOSURE = "EYE_CLOSURE"
    YAWN = "YAWN"
    HEAD_POSE = "HEAD_POSE"
    COMBINED = "COMBINED"


class RiskEventPayload(BaseModel):
    """
    Event payload sent to the backend.
    Contract: required fields for ingestion and analytics.
    """

    level: RiskLevel = Field(..., description="Risk severity")
    type: RiskType = Field(..., description="Event type")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Event time (UTC)",
    )
    session_id: Optional[str] = Field(
        None,
        description="Driver/session identifier; optional if not yet in a session",
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="EAR, MAR, head pose angles, etc.",
    )
    message: Optional[str] = Field(None, description="Optional human-readable message")

    @field_serializer("timestamp")
    def serialize_timestamp_iso_utc(self, dt: datetime) -> str:
        """Serialize as ISO 8601 with Z (UTC) for backend compatibility."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    model_config = {"json_schema_extra": {"example": {"level": "MEDIUM", "type": "YAWN", "metrics": {"mar": 0.62, "ear": 0.28}}}}
