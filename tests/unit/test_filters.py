from airwrite.trajectory.filters import PassthroughFilter
from airwrite.trajectory.stroke import StrokePoint


def test_passthrough_filter_returns_original_point() -> None:
    point = StrokePoint(x=12.5, y=33.0)
    point_filter = PassthroughFilter()

    assert point_filter.apply(point) == point
