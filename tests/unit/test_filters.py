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


def test_deadzone_filter_suppresses_micro_jitter() -> None:
    point_filter = DeadzoneFilter(deadzone=3.0, smoothing=0.0)

    first = point_filter.update(StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0))
    second = point_filter.update(StrokePoint(x=11.5, y=11.0, t=1.0, confidence=1.0))

    assert first == StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0)
    assert second is None


def test_deadzone_filter_emits_smoothed_point_after_large_move() -> None:
    point_filter = DeadzoneFilter(deadzone=3.0, smoothing=0.5, start_threshold=0.0)

    point_filter.update(StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0))
    emitted = point_filter.update(StrokePoint(x=18.0, y=10.0, t=1.0, confidence=0.8))

    assert emitted == StrokePoint(x=14.0, y=10.0, t=1.0, confidence=0.8)


def test_deadzone_filter_suppresses_pen_down_seed_until_motion_exceeds_start_threshold() -> None:
    point_filter = DeadzoneFilter(deadzone=2.0, smoothing=0.0, start_threshold=6.0)

    first = point_filter.update(StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0))
    second = point_filter.update(StrokePoint(x=13.0, y=10.0, t=1.0, confidence=1.0))
    third = point_filter.update(StrokePoint(x=18.0, y=10.0, t=2.0, confidence=1.0))

    assert first is None
    assert second is None
    assert third == StrokePoint(x=18.0, y=10.0, t=2.0, confidence=1.0)


def test_deadzone_filter_ignores_large_tracking_jump() -> None:
    point_filter = DeadzoneFilter(
        deadzone=2.0,
        smoothing=0.0,
        start_threshold=0.0,
        max_jump_distance=20.0,
    )

    point_filter.update(StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0))
    ignored = point_filter.update(StrokePoint(x=50.0, y=50.0, t=1.0, confidence=1.0))
    resumed = point_filter.update(StrokePoint(x=18.0, y=12.0, t=2.0, confidence=1.0))

    assert ignored is None
    assert resumed == StrokePoint(x=18.0, y=12.0, t=2.0, confidence=1.0)


def test_deadzone_filter_reports_whether_a_gap_can_resume_plausibly() -> None:
    point_filter = DeadzoneFilter(
        deadzone=2.0,
        smoothing=0.0,
        start_threshold=0.0,
        max_jump_distance=20.0,
    )

    point_filter.update(StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0))

    assert point_filter.can_recover_to(StrokePoint(x=24.0, y=12.0, t=1.0, confidence=1.0)) is True
    assert point_filter.can_recover_to(StrokePoint(x=45.0, y=40.0, t=1.0, confidence=1.0)) is False
