import pytest

from airwrite.tracking.hand_tracker import HandTrackerAdapter
from airwrite.tracking.landmarks import HandLandmarks, NormalizedHandDetection, Point2D


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
