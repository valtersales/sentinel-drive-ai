"""
Process frames with MediaPipe Face Landmarker (tasks API) and compute EAR, MAR, head pose.
Handles frames with no face (fallback: no metrics).
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions
from mediapipe.tasks.python.vision.core import vision_task_running_mode
from mediapipe import Image, ImageFormat

from .landmarks import (
    FrameMetrics,
    eye_aspect_ratio,
    head_pose_angles,
    mouth_aspect_ratio,
)

logger = logging.getLogger(__name__)

VisionTaskRunningMode = vision_task_running_mode.VisionTaskRunningMode


@dataclass
class FaceProcessorConfig:
    min_detection_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    max_num_faces: int = 1
    model_asset_path: Optional[str] = None


def _default_model_path() -> Optional[str]:
    # Env override (e.g. when running locally)
    env_path = __import__("os").environ.get("FACE_LANDMARKER_MODEL_PATH")
    if env_path and Path(env_path).exists():
        return env_path
    # Docker: model copied to /app at build time
    if Path("/app/face_landmarker.task").exists():
        return "/app/face_landmarker.task"
    # Local run from ai-service/: use current dir or cwd
    for candidate in (Path(__file__).resolve().parent.parent.parent / "face_landmarker.task", Path.cwd() / "face_landmarker.task"):
        if candidate.exists():
            return str(candidate)
    return None


class FaceProcessor:
    """Runs Face Landmarker and computes per-frame metrics."""

    def __init__(self, config: Optional[FaceProcessorConfig] = None):
        self.config = config or FaceProcessorConfig()
        model_path = self.config.model_asset_path or _default_model_path()
        if not model_path:
            raise FileNotFoundError(
                "Face landmarker model not found. Set FACE_LANDMARKER_MODEL_PATH or add face_landmarker.task to /app"
            )
        base_options = BaseOptions(model_asset_path=model_path)
        options = FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=VisionTaskRunningMode.IMAGE,
            num_faces=self.config.max_num_faces,
            min_face_detection_confidence=self.config.min_detection_confidence,
            min_face_presence_confidence=self.config.min_tracking_confidence,
        )
        self._face_landmarker = FaceLandmarker.create_from_options(options)
        self._frame_count = 0

    def process_frame(self, frame: np.ndarray) -> FrameMetrics:
        """
        Run face landmarker on BGR frame; return EAR, MAR, head pose.
        If no face detected, returns FrameMetrics(face_detected=False).
        """
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb)

        result = self._face_landmarker.detect(mp_image)

        if not result.face_landmarks or len(result.face_landmarks) == 0:
            return FrameMetrics(face_detected=False)

        # Use first face: list of NormalizedLandmark (indexable, .x .y)
        landmarks = result.face_landmarks[0]
        if len(landmarks) < 400:  # need enough points for our indices
            return FrameMetrics(face_detected=False)

        ear = eye_aspect_ratio(landmarks, w, h)
        mar = mouth_aspect_ratio(landmarks, w, h)
        head_pose = head_pose_angles(landmarks, w, h)

        return FrameMetrics(
            ear=ear,
            mar=mar,
            head_pose=head_pose,
            face_detected=True,
        )

    def close(self):
        if hasattr(self._face_landmarker, "close"):
            self._face_landmarker.close()


def draw_overlay(
    frame: np.ndarray,
    metrics: FrameMetrics,
    status_text: Optional[str] = None,
    status_ok: bool = True,
) -> np.ndarray:
    """
    Draw metrics (line 1) and status/alert (line 2) on frame.
    status_text: e.g. "It's all good" or "HIGH: YAWN" (same as sidebar).
    status_ok: True = green (ok), False = red (alert).
    """
    out = frame.copy()
    h, w = out.shape[:2]
    overlay = out.copy()
    cv2.rectangle(overlay, (0, 0), (w, 60), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, out, 0.5, 0, out)
    y = 24
    if metrics.face_detected:
        text = f"EAR: {metrics.ear:.2f}  MAR: {metrics.mar:.2f}" if metrics.ear is not None else "Face"
        if metrics.head_pose:
            text += f"  Tilt: {metrics.head_pose.get('tilt_deg', 0):.1f}"
        cv2.putText(out, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    else:
        cv2.putText(out, "No face detected", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
    if status_text:
        color = (0, 255, 0) if status_ok else (0, 0, 255)  # BGR: green or red
        cv2.putText(out, status_text, (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return out
