from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


REQUIRED_HAND_LANDMARKS = ("index_tip", "thumb_tip", "wrist", "middle_mcp")


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float

    def __post_init__(self) -> None:
        _require_number("x", self.x)
        _require_number("y", self.y)


@dataclass(frozen=True)
class HandLandmarks:
    index_tip: Point2D
    thumb_tip: Point2D
    wrist: Point2D
    middle_mcp: Point2D
    confidence: float
    all_points: tuple[Point2D, ...] = ()
    raw_index_tip: Point2D | None = None
    raw_thumb_tip: Point2D | None = None
    raw_wrist: Point2D | None = None
    raw_middle_mcp: Point2D | None = None

    def __post_init__(self) -> None:
        _require_confidence_in_range(self.confidence)
        if self.raw_index_tip is None:
            object.__setattr__(self, "raw_index_tip", self.index_tip)
        if self.raw_thumb_tip is None:
            object.__setattr__(self, "raw_thumb_tip", self.thumb_tip)
        if self.raw_wrist is None:
            object.__setattr__(self, "raw_wrist", self.wrist)
        if self.raw_middle_mcp is None:
            object.__setattr__(self, "raw_middle_mcp", self.middle_mcp)


@dataclass(frozen=True)
class NormalizedHandDetection:
    index_tip: Point2D
    thumb_tip: Point2D
    wrist: Point2D
    middle_mcp: Point2D
    confidence: float

    def __post_init__(self) -> None:
        _require_confidence_in_range(self.confidence)

    @classmethod
    def from_normalized_points(
        cls,
        points: Mapping[str, object],
        confidence: float,
        *,
        field_map: Mapping[str, str] | None = None,
    ) -> "NormalizedHandDetection":
        resolved_field_map = {
            landmark_name: (field_map[landmark_name] if field_map else landmark_name)
            for landmark_name in REQUIRED_HAND_LANDMARKS
        }

        normalized_points = {
            landmark_name: _point_from_mapping(
                points=points,
                landmark_name=landmark_name,
                provider_name=provider_name,
            )
            for landmark_name, provider_name in resolved_field_map.items()
        }

        return cls(
            index_tip=normalized_points["index_tip"],
            thumb_tip=normalized_points["thumb_tip"],
            wrist=normalized_points["wrist"],
            middle_mcp=normalized_points["middle_mcp"],
            confidence=confidence,
        )


def _point_from_mapping(
    *,
    points: Mapping[str, object],
    landmark_name: str,
    provider_name: str,
) -> Point2D:
    if provider_name not in points:
        raise ValueError(f"missing required landmark: {landmark_name}")

    raw_point = points[provider_name]
    if not isinstance(raw_point, tuple | list) or len(raw_point) != 2:
        raise ValueError(f"landmark {landmark_name} must be a 2-item point")

    x, y = raw_point
    _require_number(f"{landmark_name}.x", x)
    _require_number(f"{landmark_name}.y", y)
    return Point2D(x=float(x), y=float(y))


def _require_number(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{name} must be a number")


def _require_confidence_in_range(confidence: float) -> None:
    _require_number("confidence", confidence)
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")
