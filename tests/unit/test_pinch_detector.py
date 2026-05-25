from airwrite.interaction.pinch_detector import PinchDetector
from airwrite.tracking.landmarks import HandLandmarks, Point2D


def test_pinch_detector_requires_stable_frames_before_activating() -> None:
    detector = PinchDetector(down_threshold=0.30, up_threshold=0.45, stable_frames=2)
    landmarks = _make_landmarks(thumb_tip=(0.10, 0.10), index_tip=(0.20, 0.10))

    assert detector.update(landmarks) is False
    assert detector.update(landmarks) is True


def test_pinch_detector_uses_normalized_distance_scale() -> None:
    detector = PinchDetector(down_threshold=0.30, up_threshold=0.45, stable_frames=1)

    small_hand = _make_landmarks(
        thumb_tip=(0.10, 0.10),
        index_tip=(0.30, 0.10),
        wrist=(0.00, 0.00),
        middle_mcp=(0.40, 0.00),
    )
    large_hand = _make_landmarks(
        thumb_tip=(0.10, 0.10),
        index_tip=(0.30, 0.10),
        wrist=(0.00, 0.00),
        middle_mcp=(1.00, 0.00),
    )

    assert detector.update(small_hand) is False
    assert detector.update(large_hand) is True


def test_pinch_detector_uses_hysteresis_to_hold_state_until_release_threshold() -> None:
    detector = PinchDetector(down_threshold=0.30, up_threshold=0.45, stable_frames=1)
    pinched = _make_landmarks(thumb_tip=(0.10, 0.10), index_tip=(0.20, 0.10))
    still_held = _make_landmarks(thumb_tip=(0.10, 0.10), index_tip=(0.27, 0.10))
    released = _make_landmarks(thumb_tip=(0.10, 0.10), index_tip=(0.36, 0.10))

    assert detector.update(pinched) is True
    assert detector.update(still_held) is True
    assert detector.update(released) is False


def _make_landmarks(
    *,
    thumb_tip: tuple[float, float],
    index_tip: tuple[float, float],
    wrist: tuple[float, float] = (0.00, 0.00),
    middle_mcp: tuple[float, float] = (0.40, 0.00),
) -> HandLandmarks:
    return HandLandmarks(
        thumb_tip=Point2D(*thumb_tip),
        index_tip=Point2D(*index_tip),
        wrist=Point2D(*wrist),
        middle_mcp=Point2D(*middle_mcp),
        confidence=0.99,
    )
