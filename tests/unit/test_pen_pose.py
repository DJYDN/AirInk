import pytest

from airwrite.tracking.landmarks import HandLandmarks, Point2D
from airwrite.tracking.pen_pose import PenPose, PenPoseSmoother, derive_pen_pose


def test_pen_pose_smoother_damps_tip_jitter_across_frames() -> None:
    smoother = PenPoseSmoother(alpha=0.4)

    first = smoother.update(_make_pose(x=0.40, y=0.30, ratio=0.95))
    second = smoother.update(_make_pose(x=0.50, y=0.34, ratio=0.90))

    assert first.tip == Point2D(0.40, 0.30)
    assert second.tip == Point2D(0.44, 0.316)
    assert second.raw_tip == Point2D(0.44, 0.316)
    assert second.extension_ratio == pytest.approx(0.93)


def test_pen_pose_smoother_smooths_pinch_ratio() -> None:
    smoother = PenPoseSmoother(alpha=0.5)

    smoother.update(_make_pose(x=0.40, y=0.30, ratio=0.95, pinch_ratio=0.25))
    second = smoother.update(_make_pose(x=0.50, y=0.34, ratio=0.90, pinch_ratio=0.75))

    assert second.pinch_ratio == pytest.approx(0.50)


def test_pen_pose_smoother_resets_cleanly_between_strokes() -> None:
    smoother = PenPoseSmoother(alpha=0.4)

    smoother.update(_make_pose(x=0.40, y=0.30, ratio=0.95))
    smoother.reset()
    restarted = smoother.update(_make_pose(x=0.60, y=0.40, ratio=0.82))

    assert restarted.tip == Point2D(0.60, 0.40)
    assert restarted.extension_ratio == 0.82


def test_derive_pen_pose_includes_normalized_pinch_ratio() -> None:
    pose = derive_pen_pose(
        HandLandmarks(
            index_tip=Point2D(0.50, 0.40),
            thumb_tip=Point2D(0.50, 0.35),
            wrist=Point2D(0.50, 0.80),
            middle_mcp=Point2D(0.50, 0.60),
            confidence=1.0,
        )
    )

    assert pose.pinch_ratio == pytest.approx(0.25)


def _make_pose(
    *,
    x: float,
    y: float,
    ratio: float,
    pinch_ratio: float | None = None,
) -> PenPose:
    return PenPose(
        tip=Point2D(x, y),
        raw_tip=Point2D(x, y),
        source="index_chain",
        extension_ratio=ratio,
        confidence=0.99,
        pinch_ratio=pinch_ratio,
    )
