from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float


@dataclass(frozen=True)
class HandLandmarks:
    index_tip: Point2D
    thumb_tip: Point2D
    wrist: Point2D
    middle_mcp: Point2D
    confidence: float
