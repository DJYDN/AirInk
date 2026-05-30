from __future__ import annotations

import pytest

from airwrite.trajectory.filters import DeadzoneFilter, PassthroughFilter
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


def test_deadzone_filter_smooths_small_motion() -> None:
    point_filter = DeadzoneFilter(deadzone=3.0, smoothing=0.8)

    first = point_filter.update(StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0))
    second = point_filter.update(StrokePoint(x=11.5, y=11.0, t=1.0, confidence=1.0))

    assert first == StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0)
    assert second is not None
    assert second.x == pytest.approx(10.3)
    assert second.y == pytest.approx(10.2)


def test_deadzone_filter_smooths_larger_motion_with_more_follow() -> None:
    point_filter = DeadzoneFilter(deadzone=3.0, smoothing=0.5, start_threshold=0.0)

    point_filter.update(StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0))
    emitted = point_filter.update(StrokePoint(x=18.0, y=10.0, t=1.0, confidence=0.8))

    assert emitted is not None
    assert 14.0 < emitted.x < 18.0
    assert emitted.y == 10.0
    assert emitted.t == 1.0
    assert emitted.confidence == 0.8


def test_deadzone_filter_waits_for_start_threshold() -> None:
    point_filter = DeadzoneFilter(deadzone=2.0, smoothing=0.0, start_threshold=6.0)

    first = point_filter.update(StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0))
    second = point_filter.update(StrokePoint(x=13.0, y=10.0, t=1.0, confidence=1.0))
    third = point_filter.update(StrokePoint(x=18.0, y=10.0, t=2.0, confidence=1.0))

    assert first is None
    assert second is None
    assert third == StrokePoint(x=18.0, y=10.0, t=2.0, confidence=1.0)


def test_deadzone_filter_uses_max_jump_distance() -> None:
    point_filter = DeadzoneFilter(
        deadzone=2.0,
        smoothing=0.0,
        start_threshold=0.0,
        max_jump_distance=20.0,
    )

    point_filter.update(StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0))
    far_result = point_filter.update(StrokePoint(x=50.0, y=50.0, t=1.0, confidence=1.0))
    near_result = point_filter.update(StrokePoint(x=18.0, y=12.0, t=2.0, confidence=1.0))

    assert far_result is None
    assert near_result == StrokePoint(x=18.0, y=12.0, t=2.0, confidence=1.0)


def test_deadzone_filter_reports_gap_recovery() -> None:
    point_filter = DeadzoneFilter(
        deadzone=2.0,
        smoothing=0.0,
        start_threshold=0.0,
        max_jump_distance=20.0,
    )

    point_filter.update(StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0))

    assert point_filter.can_recover_to(StrokePoint(x=24.0, y=12.0, t=1.0, confidence=1.0)) is True
    assert point_filter.can_recover_to(StrokePoint(x=45.0, y=40.0, t=1.0, confidence=1.0)) is False
