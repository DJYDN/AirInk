from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StrokePoint:
    x: float
    y: float
    t: float
    confidence: float


@dataclass
class Stroke:
    points: list[StrokePoint] = field(default_factory=list)
