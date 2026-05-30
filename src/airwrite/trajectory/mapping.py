from __future__ import annotations

from dataclasses import dataclass
import os

_DEFAULT_WRITING_REGION = (0.18, 0.82, 0.15, 0.85)


def map_image_to_canvas(
    *,
    image_x: float,
    image_y: float,
    image_width: float,
    image_height: float,
    canvas_width: float,
    canvas_height: float,
    active_region: tuple[float, float, float, float] | None = None,
) -> tuple[float, float]:
    normalized_x = image_x / image_width
    normalized_y = image_y / image_height
    resolved_region = active_region if active_region is not None else _default_active_region()
    if resolved_region is not None:
        left, right, top, bottom = resolved_region
        normalized_x = _normalize_within_region(normalized_x, left, right)
        normalized_y = _normalize_within_region(normalized_y, top, bottom)

    return (
        normalized_x * canvas_width,
        normalized_y * canvas_height,
    )


def _default_active_region() -> tuple[float, float, float, float] | None:
    if (os.getenv("AIRWRITE_ENV") or "dev").strip().lower() == "test":
        return None
    raw_region = os.getenv("AIRWRITE_ACTIVE_REGION", "").strip()
    if not raw_region:
        return _DEFAULT_WRITING_REGION
    try:
        left, right, top, bottom = [float(value.strip()) for value in raw_region.split(",")]
    except ValueError:
        return _DEFAULT_WRITING_REGION
    return (left, right, top, bottom)


def _normalize_within_region(value: float, start: float, end: float) -> float:
    if end <= start:
        raise ValueError("active region end must be greater than start")

    clamped = min(max(value, start), end)
    return (clamped - start) / (end - start)


@dataclass
class RelativeMotionMapper:
    _cursor_x: float | None = None
    _cursor_y: float | None = None
    _last_tip_x: float | None = None
    _last_tip_y: float | None = None

    def hover(self, *, tip_x: float, tip_y: float) -> None:
        self._last_tip_x = tip_x
        self._last_tip_y = tip_y

    def update(
        self,
        *,
        tip_x: float,
        tip_y: float,
        image_width: float,
        image_height: float,
        canvas_width: float,
        canvas_height: float,
    ) -> tuple[float, float]:
        if self._cursor_x is None or self._cursor_y is None:
            self._cursor_x = canvas_width / 2.0
            self._cursor_y = canvas_height / 2.0

        if self._last_tip_x is None or self._last_tip_y is None:
            self._last_tip_x = tip_x
            self._last_tip_y = tip_y
            return (self._cursor_x, self._cursor_y)

        delta_x = (tip_x - self._last_tip_x) * canvas_width
        delta_y = (tip_y - self._last_tip_y) * canvas_height
        self._cursor_x = min(max(self._cursor_x + delta_x, 0.0), canvas_width)
        self._cursor_y = min(max(self._cursor_y + delta_y, 0.0), canvas_height)
        self._last_tip_x = tip_x
        self._last_tip_y = tip_y
        return (self._cursor_x, self._cursor_y)

    def reset(self) -> None:
        self._cursor_x = None
        self._cursor_y = None
        self._last_tip_x = None
        self._last_tip_y = None
