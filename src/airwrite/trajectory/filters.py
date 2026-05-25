from __future__ import annotations

from dataclasses import dataclass

from airwrite.trajectory.stroke import StrokePoint


@dataclass
class PassthroughFilter:
    def update(self, point: StrokePoint) -> StrokePoint:
        return point

    def reset(self) -> None:
        return None

    def apply(self, point: StrokePoint) -> StrokePoint:
        return self.update(point)
