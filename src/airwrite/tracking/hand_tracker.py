from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from airwrite.tracking.landmarks import HandLandmarks, NormalizedHandDetection, Point2D


@dataclass
class HandTrackerAdapter:
    min_detection_confidence: float = 0.0

    def __post_init__(self) -> None:
        if self.min_detection_confidence < 0.0 or self.min_detection_confidence > 1.0:
            raise ValueError("min_detection_confidence must be between 0.0 and 1.0")

    def from_detection(self, detection: NormalizedHandDetection) -> HandLandmarks | None:
        if detection.confidence < self.min_detection_confidence:
            return None

        return HandLandmarks(
            index_tip=_copy_point(detection.index_tip),
            thumb_tip=_copy_point(detection.thumb_tip),
            wrist=_copy_point(detection.wrist),
            middle_mcp=_copy_point(detection.middle_mcp),
            confidence=detection.confidence,
        )

    def from_normalized_points(
        self,
        points: Mapping[str, object],
        confidence: float,
        *,
        field_map: Mapping[str, str] | None = None,
    ) -> HandLandmarks | None:
        detection = NormalizedHandDetection.from_normalized_points(
            points=points,
            confidence=confidence,
            field_map=field_map,
        )
        return self.from_detection(detection)


def _copy_point(point: Point2D) -> Point2D:
    return Point2D(x=point.x, y=point.y)
