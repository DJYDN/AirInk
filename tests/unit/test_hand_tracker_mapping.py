import pytest

from airwrite.tracking.hand_tracker import HandTrackerAdapter, LandmarkSmoother
from airwrite.tracking.landmarks import HandLandmarks, NormalizedHandDetection, Point2D
from airwrite.tracking.pen_pose import derive_pen_pose


def test_hand_landmarks_expose_point_properties() -> None:
    landmarks = HandLandmarks(
        index_tip=Point2D(x=0.1, y=0.2),
        thumb_tip=Point2D(x=0.3, y=0.4),
        wrist=Point2D(x=0.5, y=0.6),
        middle_mcp=Point2D(x=0.7, y=0.8),
        confidence=0.9,
    )

    assert landmarks.index_tip == Point2D(x=0.1, y=0.2)
    assert landmarks.thumb_tip == Point2D(x=0.3, y=0.4)
    assert landmarks.wrist == Point2D(x=0.5, y=0.6)
    assert landmarks.middle_mcp == Point2D(x=0.7, y=0.8)
    assert landmarks.confidence == 0.9


def test_normalized_hand_detection_maps_provider_points_to_named_landmarks() -> None:
    detection = NormalizedHandDetection.from_normalized_points(
        points={
            "index_fingertip": (0.1, 0.2),
            "thumb_fingertip": (0.3, 0.4),
            "hand_wrist": (0.5, 0.6),
            "middle_knuckle": (0.7, 0.8),
        },
        confidence=0.9,
        field_map={
            "index_tip": "index_fingertip",
            "thumb_tip": "thumb_fingertip",
            "wrist": "hand_wrist",
            "middle_mcp": "middle_knuckle",
        },
    )

    assert detection == NormalizedHandDetection(
        index_tip=Point2D(x=0.1, y=0.2),
        thumb_tip=Point2D(x=0.3, y=0.4),
        wrist=Point2D(x=0.5, y=0.6),
        middle_mcp=Point2D(x=0.7, y=0.8),
        confidence=0.9,
    )


def test_hand_tracker_adapter_maps_typed_detection_to_hand_landmarks() -> None:
    adapter = HandTrackerAdapter(min_detection_confidence=0.6)
    detection = NormalizedHandDetection(
        index_tip=Point2D(x=0.1, y=0.2),
        thumb_tip=Point2D(x=0.3, y=0.4),
        wrist=Point2D(x=0.5, y=0.6),
        middle_mcp=Point2D(x=0.7, y=0.8),
        confidence=0.9,
    )

    result = adapter.from_detection(detection)

    assert result == HandLandmarks(
        index_tip=Point2D(x=0.1, y=0.2),
        thumb_tip=Point2D(x=0.3, y=0.4),
        wrist=Point2D(x=0.5, y=0.6),
        middle_mcp=Point2D(x=0.7, y=0.8),
        confidence=0.9,
    )


def test_hand_tracker_adapter_preserves_raw_points_when_smoothed_points_differ() -> None:
    adapter = HandTrackerAdapter(min_detection_confidence=0.6)
    detection = NormalizedHandDetection(
        index_tip=Point2D(x=0.3, y=0.2),
        thumb_tip=Point2D(x=0.2, y=0.4),
        wrist=Point2D(x=0.5, y=0.6),
        middle_mcp=Point2D(x=0.7, y=0.8),
        confidence=0.9,
    )

    result = adapter.from_detection(
        detection,
        raw_points={
            "index_tip": Point2D(x=0.4, y=0.2),
            "thumb_tip": Point2D(x=0.3, y=0.4),
            "wrist": Point2D(x=0.5, y=0.6),
            "middle_mcp": Point2D(x=0.7, y=0.8),
        },
    )

    assert result is not None
    assert result.index_tip == Point2D(x=0.3, y=0.2)
    assert result.raw_index_tip == Point2D(x=0.4, y=0.2)
    assert result.raw_index_tip != result.index_tip


def test_hand_tracker_adapter_returns_none_below_min_detection_confidence() -> None:
    adapter = HandTrackerAdapter(min_detection_confidence=0.6)
    detection = NormalizedHandDetection(
        index_tip=Point2D(x=0.1, y=0.2),
        thumb_tip=Point2D(x=0.3, y=0.4),
        wrist=Point2D(x=0.5, y=0.6),
        middle_mcp=Point2D(x=0.7, y=0.8),
        confidence=0.59,
    )

    result = adapter.from_detection(detection)

    assert result is None


def test_normalized_hand_detection_rejects_missing_required_landmark() -> None:
    with pytest.raises(ValueError, match="missing required landmark: wrist"):
        NormalizedHandDetection.from_normalized_points(
            points={
                "index_tip": (0.1, 0.2),
                "thumb_tip": (0.3, 0.4),
                "middle_mcp": (0.7, 0.8),
            },
            confidence=0.9,
        )


def test_normalized_hand_detection_rejects_malformed_point_shape() -> None:
    with pytest.raises(ValueError, match="landmark index_tip must be a 2-item point"):
        NormalizedHandDetection.from_normalized_points(
            points={
                "index_tip": (0.1,),
                "thumb_tip": (0.3, 0.4),
                "wrist": (0.5, 0.6),
                "middle_mcp": (0.7, 0.8),
            },
            confidence=0.9,
        )


def test_normalized_hand_detection_rejects_out_of_bounds_confidence() -> None:
    with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
        NormalizedHandDetection(
            index_tip=Point2D(x=0.1, y=0.2),
            thumb_tip=Point2D(x=0.3, y=0.4),
            wrist=Point2D(x=0.5, y=0.6),
            middle_mcp=Point2D(x=0.7, y=0.8),
            confidence=1.1,
        )


def test_landmark_smoother_applies_exponential_smoothing_to_points() -> None:
    smoother = LandmarkSmoother(alpha=0.5)

    first = smoother.update(
        {
            "index_tip": Point2D(x=0.2, y=0.2),
            "thumb_tip": Point2D(x=0.1, y=0.2),
        }
    )
    second = smoother.update(
        {
            "index_tip": Point2D(x=0.4, y=0.2),
            "thumb_tip": Point2D(x=0.3, y=0.2),
        }
    )

    assert first["index_tip"] == Point2D(x=0.2, y=0.2)
    assert second["index_tip"].x == pytest.approx(0.3)
    assert second["index_tip"].y == pytest.approx(0.2)
    assert second["thumb_tip"].x == pytest.approx(0.2)
    assert second["thumb_tip"].y == pytest.approx(0.2)


def test_derive_pen_pose_uses_multiple_index_joints() -> None:
    landmarks = HandLandmarks(
        index_tip=Point2D(x=0.60, y=0.20),
        thumb_tip=Point2D(x=0.48, y=0.52),
        wrist=Point2D(x=0.50, y=0.82),
        middle_mcp=Point2D(x=0.52, y=0.60),
        confidence=0.95,
        all_points=(
            Point2D(x=0.50, y=0.82),
            Point2D(x=0.48, y=0.76),
            Point2D(x=0.47, y=0.68),
            Point2D(x=0.46, y=0.58),
            Point2D(x=0.46, y=0.50),
            Point2D(x=0.54, y=0.62),
            Point2D(x=0.57, y=0.46),
            Point2D(x=0.59, y=0.31),
            Point2D(x=0.60, y=0.20),
        ),
    )

    pose = derive_pen_pose(landmarks)

    assert pose.source == "index_chain"
    assert pose.raw_tip == Point2D(x=0.60, y=0.20)
    assert pose.tip.x == pytest.approx(0.594, abs=0.001)
    assert pose.tip.y == pytest.approx(0.259, abs=0.001)
    assert pose.extension_ratio == pytest.approx(0.999, abs=0.001)


def test_derive_pen_pose_treats_diagonal_straight_finger_as_extended() -> None:
    landmarks = HandLandmarks(
        index_tip=Point2D(x=0.25, y=0.30),
        thumb_tip=Point2D(x=0.48, y=0.52),
        wrist=Point2D(x=0.50, y=0.82),
        middle_mcp=Point2D(x=0.52, y=0.60),
        confidence=0.95,
        all_points=(
            Point2D(x=0.50, y=0.82),
            Point2D(x=0.48, y=0.76),
            Point2D(x=0.47, y=0.68),
            Point2D(x=0.46, y=0.58),
            Point2D(x=0.46, y=0.50),
            Point2D(x=0.40, y=0.60),
            Point2D(x=0.35, y=0.50),
            Point2D(x=0.30, y=0.40),
            Point2D(x=0.25, y=0.30),
        ),
    )

    pose = derive_pen_pose(landmarks)

    assert pose.extension_ratio > 0.9


def test_derive_pen_pose_treats_curled_index_finger_as_not_extended() -> None:
    landmarks = HandLandmarks(
        index_tip=Point2D(x=0.46, y=0.50),
        thumb_tip=Point2D(x=0.48, y=0.52),
        wrist=Point2D(x=0.50, y=0.82),
        middle_mcp=Point2D(x=0.52, y=0.60),
        confidence=0.95,
        all_points=(
            Point2D(x=0.50, y=0.82),
            Point2D(x=0.48, y=0.76),
            Point2D(x=0.47, y=0.68),
            Point2D(x=0.46, y=0.58),
            Point2D(x=0.46, y=0.50),
            Point2D(x=0.40, y=0.60),
            Point2D(x=0.36, y=0.52),
            Point2D(x=0.40, y=0.48),
            Point2D(x=0.46, y=0.50),
        ),
    )

    pose = derive_pen_pose(landmarks)

    assert pose.extension_ratio < 0.8
