from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from airwrite.trajectory.stroke import StrokePoint


@dataclass
class PassthroughFilter:
    def update(self, point: StrokePoint) -> StrokePoint:
        return point

    def reset(self) -> None:
        return None

    def apply(self, point: StrokePoint) -> StrokePoint:
        return self.update(point)

    def prime(self, point: StrokePoint) -> None:
        return None


@dataclass
class DeadzoneFilter:
    deadzone: float
    smoothing: float = 0.0
    start_threshold: float = 0.0
    max_jump_distance: float | None = None

    def __post_init__(self) -> None:
        if self.deadzone < 0.0:
            raise ValueError("deadzone must be non-negative")
        if self.smoothing < 0.0 or self.smoothing > 1.0:
            raise ValueError("smoothing must be between 0.0 and 1.0")
        if self.start_threshold < 0.0:
            raise ValueError("start_threshold must be non-negative")
        if self.max_jump_distance is not None and self.max_jump_distance <= 0.0:
            raise ValueError("max_jump_distance must be positive when set")
        self._last_emitted: StrokePoint | None = None
        self._seed_point: StrokePoint | None = None

    def update(self, point: StrokePoint) -> StrokePoint | None:
        if self._last_emitted is None:
            if self.start_threshold <= 0.0:
                self._last_emitted = point
                return point

            if self._seed_point is None:
                self._seed_point = point
                return None

            seed_distance = hypot(point.x - self._seed_point.x, point.y - self._seed_point.y)
            if seed_distance < self.start_threshold:
                return None

            self._seed_point = None
            self._last_emitted = point
            return point

        distance = hypot(point.x - self._last_emitted.x, point.y - self._last_emitted.y)
        if self.max_jump_distance is not None and distance > self.max_jump_distance:
            return None
        if distance < self.deadzone:
            return None

        alpha = 1.0 - self.smoothing
        filtered_point = StrokePoint(
            x=self._last_emitted.x + (point.x - self._last_emitted.x) * alpha,
            y=self._last_emitted.y + (point.y - self._last_emitted.y) * alpha,
            t=point.t,
            confidence=point.confidence,
        )
        self._last_emitted = filtered_point
        return filtered_point

    def reset(self) -> None:
        self._last_emitted = None
        self._seed_point = None

    def prime(self, point: StrokePoint) -> None:
        if self._last_emitted is None:
            self._seed_point = point

    def can_recover_to(self, point: StrokePoint) -> bool:
        if self._last_emitted is None:
            return False
        if self.max_jump_distance is None:
            return True
        return hypot(point.x - self._last_emitted.x, point.y - self._last_emitted.y) <= self.max_jump_distance

    def apply(self, point: StrokePoint) -> StrokePoint | None:
        return self.update(point)
