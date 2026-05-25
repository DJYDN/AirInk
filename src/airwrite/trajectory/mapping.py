from __future__ import annotations

from airwrite.trajectory.stroke import StrokePoint


def map_image_to_canvas(
    *,
    image_x: float,
    image_y: float,
    image_width: float,
    image_height: float,
    canvas_width: float,
    canvas_height: float,
) -> StrokePoint:
    return StrokePoint(
        x=image_x / image_width * canvas_width,
        y=image_y / image_height * canvas_height,
    )
