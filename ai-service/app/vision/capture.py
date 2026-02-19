"""Video capture (camera or stream) and frame iteration."""
import logging
from typing import Generator, Optional, Union

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def open_video_source(source: Union[str, int]):
    """
    Open video capture from camera index (int) or URL/path (str).
    Returns cv2.VideoCapture or None if failed.
    """
    if isinstance(source, str):
        if source.isdigit():
            source = int(source)
        else:
            # URL (rtsp, http, etc.) or file path
            pass
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logger.warning("Could not open video source: %s", source)
        return None
    return cap


def frame_generator(
    source: Union[str, int],
    max_frames: Optional[int] = None,
    resize: Optional[tuple] = None,
) -> Generator[tuple[Optional[np.ndarray], int], None, None]:
    """
    Yield (frame, frame_index). frame is None on read error or end.
    resize: (width, height) to resize each frame.
    """
    cap = open_video_source(source)
    if cap is None:
        yield None, 0
        return
    try:
        idx = 0
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                yield None, idx
                break
            if resize:
                frame = cv2.resize(frame, resize)
            yield frame, idx
            idx += 1
            if max_frames is not None and idx >= max_frames:
                break
    finally:
        cap.release()
