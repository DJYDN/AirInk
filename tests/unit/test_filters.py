from airwrite.trajectory.filters import PassthroughFilter
from airwrite.trajectory.stroke import StrokePoint


def test_passthrough_filter_update_returns_original_point() -> None:
    point = StrokePoint(x=12.5, y=33.0, t=1.25, confidence=0.75)
    point_filter = PassthroughFilter()

    assert point_filter.update(point) == point


def test_passthrough_filter_reset_keeps_filter_ready_for_reuse() -> None:
    point = StrokePoint(x=5.0, y=7.5, t=2.5, confidence=0.5)
    point_filter = PassthroughFilter()

    point_filter.reset()

    assert point_filter.update(point) == point
