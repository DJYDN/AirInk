from __future__ import annotations

from dataclasses import dataclass

from airwrite.tracking.landmarks import HandLandmarks, Point2D


@dataclass
class HandTrackerAdapter:
    min_detection_confidence: float = 0.0

    def from_normalized_points(
        self,
        points: dict[str, tuple[float, float]],
        confidence: float,
    ) -> HandLandmarks | None:
        if confidence < self.min_detection_confidence:
            return None

        return HandLandmarks(
            index_tip=_point_from_tuple(points["index_tip"]),
            thumb_tip=_point_from_tuple(points["thumb_tip"]),
            wrist=_point_from_tuple(points["wrist"]),
            middle_mcp=_point_from_tuple(points["middle_mcp"]),
            confidence=confidence,
        )


def _point_from_tuple(point: tuple[float, float]) -> Point2D:
    return Point2D(x=point[0], y=point[1])
