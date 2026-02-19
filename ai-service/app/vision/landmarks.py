"""
Facial landmark indices for MediaPipe Face Mesh (468 points).
Conventions from EAR/MAR literature (e.g. Soukupová & Čech for EAR).
"""
import math
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

# MediaPipe Face Mesh indices (0-based)
# Left eye: 33, 160, 158, 133, 153, 144
# Right eye: 362, 385, 387, 263, 373, 380
LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

# Mouth: 6-point MAR = (dist(13,312)+dist(14,317))/(2*dist(78,308))
# 13, 14: upper lip; 312, 317: lower lip; 78, 308: corners
MOUTH_INDICES = [13, 14, 312, 317, 78, 308]

# Nose tip and base for head pose (optional ref)
NOSE_TIP_INDEX = 4
LEFT_EYE_CENTER = 468  # not in 468; use avg of left eye
RIGHT_EYE_CENTER = 468


def _get_lm(landmarks, index: int):
    """Support both legacy (landmarks.landmark[i]) and tasks API (landmarks[i])."""
    if hasattr(landmarks, "landmark"):
        return landmarks.landmark[index]
    return landmarks[index]


def _landmark_point(landmarks, index: int, frame_width: int, frame_height: int):
    """Return (x, y) in pixel coordinates."""
    lm = _get_lm(landmarks, index)
    x = int(lm.x * frame_width)
    y = int(lm.y * frame_height)
    return x, y


def _landmark_xy_normalized(landmarks, index: int):
    """Return (x, y) normalized [0,1]."""
    lm = _get_lm(landmarks, index)
    return lm.x, lm.y


def eye_aspect_ratio(landmarks, frame_width: int, frame_height: int) -> Optional[float]:
    """
    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    Left: p1=33, p2=160, p3=158, p4=133, p5=153, p6=144
    Right: p1=362, p2=385, p3=387, p4=263, p5=373, p6=380
    """
    def _ear(indices):
        p1, p2, p3, p4, p5, p6 = [_landmark_point(landmarks, i, frame_width, frame_height) for i in indices]
        v1 = np.linalg.norm(np.array(p2) - np.array(p6))
        v2 = np.linalg.norm(np.array(p3) - np.array(p5))
        h = np.linalg.norm(np.array(p1) - np.array(p4))
        if h < 1e-6:
            return None
        return (v1 + v2) / (2.0 * h)

    left = _ear(LEFT_EYE_INDICES)
    right = _ear(RIGHT_EYE_INDICES)
    if left is None or right is None:
        return None
    return (left + right) / 2.0


def mouth_aspect_ratio(landmarks, frame_width: int, frame_height: int) -> Optional[float]:
    """
    MAR = (vertical_left + vertical_right) / (2 * horizontal).
    6-point formula: 13, 14 = upper lip; 312, 317 = lower lip; 78, 308 = mouth corners.
    Typically gives ~0.2–0.4 closed, ~0.5+ for yawn; more robust than single mid-line.
    """
    upper_left = _landmark_point(landmarks, 13, frame_width, frame_height)
    upper_right = _landmark_point(landmarks, 14, frame_width, frame_height)
    lower_left = _landmark_point(landmarks, 312, frame_width, frame_height)
    lower_right = _landmark_point(landmarks, 317, frame_width, frame_height)
    left_c = _landmark_point(landmarks, 78, frame_width, frame_height)
    right_c = _landmark_point(landmarks, 308, frame_width, frame_height)
    vertical_left = np.linalg.norm(np.array(upper_left) - np.array(lower_left))
    vertical_right = np.linalg.norm(np.array(upper_right) - np.array(lower_right))
    horizontal = np.linalg.norm(np.array(left_c) - np.array(right_c))
    if horizontal < 1e-6:
        return None
    return (vertical_left + vertical_right) / (2.0 * horizontal)


def head_pose_angles(landmarks, frame_width: int, frame_height: int) -> Optional[dict]:
    """
    Estimate head tilt (roll) and rotation (yaw) from face landmarks.
    Returns dict with keys: tilt_deg (roll), yaw_deg (approx).
    """
    # Use nose tip, nose base, left/right eye centers
    lm_nose = _get_lm(landmarks, NOSE_TIP_INDEX)
    nose_tip = np.array([lm_nose.x, lm_nose.y])
    left_eye = np.array([
        np.mean([_get_lm(landmarks, i).x for i in LEFT_EYE_INDICES]),
        np.mean([_get_lm(landmarks, i).y for i in LEFT_EYE_INDICES]),
    ])
    right_eye = np.array([
        np.mean([_get_lm(landmarks, i).x for i in RIGHT_EYE_INDICES]),
        np.mean([_get_lm(landmarks, i).y for i in RIGHT_EYE_INDICES]),
    ])
    # Tilt (roll): angle of line between eyes w.r.t. horizontal
    eye_vec = right_eye - left_eye
    tilt_rad = math.atan2(eye_vec[1], eye_vec[0])
    tilt_deg = math.degrees(tilt_rad)
    # Yaw: approximate from nose offset from eye center
    eye_center = (left_eye + right_eye) / 2
    nose_offset = nose_tip[0] - eye_center[0]
    yaw_deg = np.clip(nose_offset * 60, -45, 45)  # rough scale
    return {"tilt_deg": tilt_deg, "yaw_deg": float(yaw_deg)}


@dataclass
class FrameMetrics:
    """Metrics extracted from one frame."""

    ear: Optional[float] = None
    mar: Optional[float] = None
    head_pose: Optional[dict] = None
    face_detected: bool = False

    def to_dict(self) -> dict:
        d = {"face_detected": self.face_detected}
        if self.ear is not None:
            d["ear"] = round(self.ear, 4)
        if self.mar is not None:
            d["mar"] = round(self.mar, 4)
        if self.head_pose:
            d["head_pose"] = {k: round(v, 2) for k, v in self.head_pose.items()}
        return d
