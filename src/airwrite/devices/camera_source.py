from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import os
from typing import Any, Iterator

from numpy import ndarray


@dataclass
class CameraFrame:
    data: ndarray
    index: int


class CameraSource(ABC):
    @abstractmethod
    def frames(self) -> Iterator[CameraFrame]:
        """Yield frames from the configured source."""

    def close(self) -> None:
        """Release any backing resources when a real device exists."""


@dataclass
class OpenCVCameraSource(CameraSource):
    camera_index: int
    width: int
    height: int
    fps: int
    _capture: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        import cv2

        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        capture = cv2.VideoCapture(self.camera_index, backend)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        capture.set(cv2.CAP_PROP_FPS, self.fps)

        if not capture.isOpened():
            capture.release()
            raise RuntimeError(f"Unable to open camera index {self.camera_index}")

        self._capture = capture

    def frames(self) -> Iterator[CameraFrame]:
        frame_index = 0
        while True:
            ok, frame = self._capture.read()
            if not ok:
                return

            yield CameraFrame(data=frame, index=frame_index)
            frame_index += 1

    def close(self) -> None:
        self._capture.release()
