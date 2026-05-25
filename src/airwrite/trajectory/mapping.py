from __future__ import annotations


def map_image_to_canvas(
    *,
    image_x: float,
    image_y: float,
    image_width: float,
    image_height: float,
    canvas_width: float,
    canvas_height: float,
) -> tuple[float, float]:
    return (
        image_x / image_width * canvas_width,
        image_y / image_height * canvas_height,
    )
