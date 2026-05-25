from airwrite.trajectory.mapping import map_image_to_canvas
from airwrite.trajectory.stroke import Stroke, StrokePoint


def test_map_image_to_canvas_scales_coordinates_linearly() -> None:
    mapped = map_image_to_canvas(
        image_x=320,
        image_y=120,
        image_width=640,
        image_height=480,
        canvas_width=800,
        canvas_height=600,
    )

    assert mapped == StrokePoint(x=400.0, y=150.0)


def test_stroke_preserves_point_sequence() -> None:
    points = [StrokePoint(x=10.0, y=20.0), StrokePoint(x=30.0, y=40.0)]
    stroke = Stroke(points=points)

    assert stroke.points == points

