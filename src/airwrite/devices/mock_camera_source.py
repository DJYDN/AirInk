from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np

from airwrite.devices.camera_source import CameraFrame, CameraSource


@dataclass
class MockCameraSource(CameraSource):
    frame_size: tuple[int, int]
    frame_count: int

    def frames(self) -> Iterator[CameraFrame]:
        width, height = self.frame_size

        for index in range(self.frame_count):
            yield CameraFrame(
                data=np.zeros((height, width, 3), dtype=np.uint8),
                index=index,
            )
