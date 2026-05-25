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

    assert mapped == (400.0, 150.0)


def test_stroke_preserves_point_sequence_with_timestamps_and_confidence() -> None:
    points = [
        StrokePoint(x=10.0, y=20.0, t=1.5, confidence=0.9),
        StrokePoint(x=30.0, y=40.0, t=2.0, confidence=0.8),
    ]
    stroke = Stroke(points=points)

    assert stroke.points == points
    assert stroke.points[0].t == 1.5
    assert stroke.points[1].confidence == 0.8


def test_stroke_exposes_mutable_point_collection_without_frozen_dataclass_signal() -> None:
    stroke = Stroke()

    stroke.points.append(StrokePoint(x=5.0, y=6.0, t=0.1, confidence=1.0))

    assert stroke.points == [StrokePoint(x=5.0, y=6.0, t=0.1, confidence=1.0)]
