from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot

from airwrite.tracking.landmarks import HandLandmarks


@dataclass
class PinchDetector:
    down_threshold: float
    up_threshold: float
    stable_frames: int = 1
    _is_pinching: bool = field(default=False, init=False, repr=False)
    _pending_state: bool | None = field(default=None, init=False, repr=False)
    _pending_frames: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.stable_frames < 1:
            raise ValueError("stable_frames must be at least 1")
        if self.down_threshold < 0.0 or self.up_threshold < 0.0:
            raise ValueError("thresholds must be non-negative")
        if self.down_threshold > self.up_threshold:
            raise ValueError("down_threshold must be less than or equal to up_threshold")

    def update(self, landmarks: HandLandmarks) -> bool:
        normalized_distance = _distance(landmarks.thumb_tip, landmarks.index_tip) / _distance(
            landmarks.wrist,
            landmarks.middle_mcp,
        )
        next_state = self._next_state(normalized_distance)

        if next_state == self._is_pinching:
            self._pending_state = None
            self._pending_frames = 0
            return self._is_pinching

        if self._pending_state != next_state:
            self._pending_state = next_state
            self._pending_frames = 1
        else:
            self._pending_frames += 1

        if self._pending_frames >= self.stable_frames:
            self._is_pinching = next_state
            self._pending_state = None
            self._pending_frames = 0

        return self._is_pinching

    def _next_state(self, normalized_distance: float) -> bool:
        if self._is_pinching:
            return normalized_distance <= self.up_threshold
        return normalized_distance <= self.down_threshold


def _distance(first: object, second: object) -> float:
    distance = hypot(first.x - second.x, first.y - second.y)
    if distance == 0.0:
        raise ValueError("pinch normalization scale must be greater than zero")
    return distance
