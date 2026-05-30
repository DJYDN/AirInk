from __future__ import annotations

import pytest

from airwrite.trajectory.mapping import RelativeMotionMapper, map_image_to_canvas
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


def test_map_image_to_canvas_can_focus_on_active_region() -> None:
    mapped = map_image_to_canvas(
        image_x=96,
        image_y=96,
        image_width=640,
        image_height=480,
        canvas_width=800,
        canvas_height=600,
        active_region=(0.15, 0.85, 0.20, 0.80),
    )

    assert mapped == (0.0, 0.0)


def test_map_image_to_canvas_normalizes_center_of_active_region() -> None:
    mapped = map_image_to_canvas(
        image_x=320,
        image_y=180,
        image_width=640,
        image_height=360,
        canvas_width=100,
        canvas_height=100,
        active_region=(0.25, 0.75, 0.25, 0.75),
    )

    assert mapped == (50.0, 50.0)


def test_map_image_to_canvas_clamps_to_active_region() -> None:
    mapped = map_image_to_canvas(
        image_x=0,
        image_y=360,
        image_width=640,
        image_height=360,
        canvas_width=100,
        canvas_height=100,
        active_region=(0.25, 0.75, 0.25, 0.75),
    )

    assert mapped == (0.0, 100.0)


def test_map_image_to_canvas_rejects_invalid_active_region() -> None:
    with pytest.raises(ValueError):
        map_image_to_canvas(
            image_x=10,
            image_y=10,
            image_width=100,
            image_height=100,
            canvas_width=100,
            canvas_height=100,
            active_region=(0.5, 0.5, 0.0, 1.0),
        )


def test_relative_motion_mapper_starts_at_canvas_center() -> None:
    mapper = RelativeMotionMapper()

    assert mapper.update(
        tip_x=0.5,
        tip_y=0.5,
        image_width=640,
        image_height=360,
        canvas_width=100,
        canvas_height=80,
    ) == (50.0, 40.0)


def test_relative_motion_mapper_accumulates_normalized_delta() -> None:
    mapper = RelativeMotionMapper()
    mapper.update(
        tip_x=0.5,
        tip_y=0.5,
        image_width=640,
        image_height=360,
        canvas_width=100,
        canvas_height=80,
    )

    assert mapper.update(
        tip_x=0.6,
        tip_y=0.25,
        image_width=640,
        image_height=360,
        canvas_width=100,
        canvas_height=80,
    ) == pytest.approx((60.0, 20.0))


def test_stroke_preserves_point_sequence_with_timestamps_and_confidence() -> None:
    points = [
        StrokePoint(x=10.0, y=20.0, t=1.5, confidence=0.9),
        StrokePoint(x=30.0, y=40.0, t=2.0, confidence=0.8),
    ]
    stroke = Stroke(points=points)

    assert stroke.points == points
    assert stroke.points[0].t == 1.5
    assert stroke.points[1].confidence == 0.8


def test_stroke_add_point_appends_to_mutable_point_collection() -> None:
    stroke = Stroke()
    point = StrokePoint(x=5.0, y=6.0, t=0.1, confidence=1.0)

    stroke.add_point(point)

    assert stroke.points == [point]
