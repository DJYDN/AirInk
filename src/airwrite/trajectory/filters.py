from __future__ import annotations

from dataclasses import dataclass

from airwrite.trajectory.stroke import StrokePoint


@dataclass
class PassthroughFilter:
    def apply(self, point: StrokePoint) -> StrokePoint:
        return point
