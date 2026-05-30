from airwrite.interaction.gesture_state import GestureClassifier, GestureState
from airwrite.tracking.landmarks import HandLandmarks, Point2D
from airwrite.tracking.pen_pose import PenPose


def test_gesture_classifier_requires_stable_extension_before_drawing() -> None:
    classifier = GestureClassifier(
        stable_frames=2,
        fist_ratio_threshold=0.9,
        extended_ratio_threshold=1.4,
    )

    assert classifier.update(_make_pose(0.8)) is GestureState.FIST
    assert classifier.update(_make_pose(1.2)) is GestureState.ARMING_DOWN
    assert classifier.update(_make_pose(1.45)) is GestureState.ARMING_DOWN
    assert classifier.update(_make_pose(1.46)) is GestureState.DRAWING


def test_gesture_classifier_requires_stable_fist_before_pen_up() -> None:
    classifier = GestureClassifier(
        stable_frames=2,
        fist_ratio_threshold=0.9,
        extended_ratio_threshold=1.4,
    )
    extended = _make_pose(1.5)
    fist = _make_pose(0.8)

    assert classifier.update(extended) is GestureState.ARMING_DOWN
    assert classifier.update(extended) is GestureState.DRAWING
    assert classifier.update(fist) is GestureState.ARMING_UP
    assert classifier.update(fist) is GestureState.FIST


def test_gesture_classifier_reports_hand_lost_when_landmarks_are_missing() -> None:
    classifier = GestureClassifier(
        stable_frames=2,
        fist_ratio_threshold=0.9,
        extended_ratio_threshold=1.4,
    )

    assert classifier.update(None) is GestureState.HAND_LOST


def test_gesture_classifier_holds_drawing_across_brief_hand_loss() -> None:
    classifier = GestureClassifier(
        stable_frames=1,
        fist_ratio_threshold=0.9,
        extended_ratio_threshold=1.4,
        hand_loss_grace_frames=2,
    )

    assert classifier.update(_make_pose(1.5)) is GestureState.DRAWING
    assert classifier.update(None) is GestureState.DRAWING
    assert classifier.update(None) is GestureState.DRAWING
    assert classifier.update(None) is GestureState.HAND_LOST


def test_gesture_classifier_recovers_same_stroke_after_brief_hand_loss() -> None:
    classifier = GestureClassifier(
        stable_frames=1,
        fist_ratio_threshold=0.9,
        extended_ratio_threshold=1.4,
        hand_loss_grace_frames=2,
    )

    assert classifier.update(_make_pose(1.5)) is GestureState.DRAWING
    assert classifier.update(None) is GestureState.DRAWING
    assert classifier.update(_make_pose(1.55)) is GestureState.DRAWING


def test_gesture_classifier_enters_arming_up_when_extended_pose_becomes_uncertain() -> None:
    classifier = GestureClassifier(
        stable_frames=2,
        fist_ratio_threshold=0.9,
        extended_ratio_threshold=1.4,
        hand_loss_grace_frames=2,
    )

    assert classifier.update(_make_pose(1.45)) is GestureState.ARMING_DOWN
    assert classifier.update(_make_pose(1.50)) is GestureState.DRAWING
    assert classifier.update(_make_pose(1.15)) is GestureState.ARMING_UP


def test_gesture_classifier_stops_inking_when_extended_pose_curls_back() -> None:
    classifier = GestureClassifier(
        stable_frames=1,
        fist_ratio_threshold=0.9,
        extended_ratio_threshold=1.4,
        hand_loss_grace_frames=2,
    )

    assert classifier.update(_make_pose(1.5)) is GestureState.DRAWING
    assert classifier.update(_make_pose(1.1)) is GestureState.ARMING_UP


def _make_landmarks(
    *,
    index_tip: tuple[float, float],
    wrist: tuple[float, float] = (0.50, 0.80),
    middle_mcp: tuple[float, float] = (0.50, 0.60),
) -> HandLandmarks:
    return HandLandmarks(
        index_tip=Point2D(*index_tip),
        thumb_tip=Point2D(0.42, 0.60),
        wrist=Point2D(*wrist),
        middle_mcp=Point2D(*middle_mcp),
        confidence=0.99,
    )


def _make_pose(extension_ratio: float) -> PenPose:
    return PenPose(
        tip=Point2D(0.50, 0.30),
        raw_tip=Point2D(0.50, 0.30),
        source="index_chain",
        extension_ratio=extension_ratio,
        confidence=0.99,
    )
