from airwrite.tracking.hand_tracker import HandTrackerAdapter
from airwrite.tracking.landmarks import HandLandmarks, Point2D


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


def test_hand_tracker_adapter_maps_normalized_points_to_hand_landmarks() -> None:
    adapter = HandTrackerAdapter(min_detection_confidence=0.6)

    result = adapter.from_normalized_points(
        points={
            "index_tip": (0.1, 0.2),
            "thumb_tip": (0.3, 0.4),
            "wrist": (0.5, 0.6),
            "middle_mcp": (0.7, 0.8),
        },
        confidence=0.9,
    )

    assert result == HandLandmarks(
        index_tip=Point2D(x=0.1, y=0.2),
        thumb_tip=Point2D(x=0.3, y=0.4),
        wrist=Point2D(x=0.5, y=0.6),
        middle_mcp=Point2D(x=0.7, y=0.8),
        confidence=0.9,
    )


def test_hand_tracker_adapter_returns_none_below_min_detection_confidence() -> None:
    adapter = HandTrackerAdapter(min_detection_confidence=0.6)

    result = adapter.from_normalized_points(
        points={
            "index_tip": (0.1, 0.2),
            "thumb_tip": (0.3, 0.4),
            "wrist": (0.5, 0.6),
            "middle_mcp": (0.7, 0.8),
        },
        confidence=0.59,
    )

    assert result is None
