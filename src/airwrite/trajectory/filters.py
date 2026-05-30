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
            return self._initialize(point)

        distance = hypot(point.x - self._last_emitted.x, point.y - self._last_emitted.y)
        if self.max_jump_distance is not None and distance > self.max_jump_distance:
            return None

        if distance < self.deadzone:
            filtered_point = self._blend_toward(point, alpha=self._micro_motion_alpha())
            self._last_emitted = filtered_point
            return filtered_point

        filtered_point = self._blend_toward(point, alpha=self._motion_alpha(distance))
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

    def _initialize(self, point: StrokePoint) -> StrokePoint | None:
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

    def _micro_motion_alpha(self) -> float:
        return max(0.02, min(0.20, 1.0 - self.smoothing))

    def _motion_alpha(self, distance: float) -> float:
        base_alpha = 1.0 - self.smoothing
        if self.deadzone <= 0.0:
            return max(0.05, min(1.0, base_alpha))

        speed_boost = min(1.0, distance / (self.deadzone * 12.0))
        adaptive_alpha = base_alpha + (1.0 - base_alpha) * speed_boost
        return max(0.05, min(1.0, adaptive_alpha))

    def _blend_toward(self, point: StrokePoint, *, alpha: float) -> StrokePoint:
        assert self._last_emitted is not None
        return StrokePoint(
            x=self._last_emitted.x + (point.x - self._last_emitted.x) * alpha,
            y=self._last_emitted.y + (point.y - self._last_emitted.y) * alpha,
            t=point.t,
            confidence=point.confidence,
        )
