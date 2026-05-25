from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from airwrite.devices.camera_source import CameraFrame, CameraSource, FrameData


@dataclass
class MockCameraSource(CameraSource):
    frame_size: tuple[int, int]
    frame_count: int

    def frames(self) -> Iterator[CameraFrame]:
        width, height = self.frame_size
        frame_data = FrameData(shape=(height, width, 3), fill_value=0)

        for index in range(self.frame_count):
            yield CameraFrame(data=frame_data, index=index)
