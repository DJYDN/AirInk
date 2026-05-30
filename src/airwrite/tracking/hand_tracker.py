from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Mapping

from airwrite.tracking.landmarks import HandLandmarks, NormalizedHandDetection, Point2D


@dataclass
class HandTrackerAdapter:
    min_detection_confidence: float = 0.0

    def __post_init__(self) -> None:
        if self.min_detection_confidence < 0.0 or self.min_detection_confidence > 1.0:
            raise ValueError("min_detection_confidence must be between 0.0 and 1.0")

    def from_detection(
        self,
        detection: NormalizedHandDetection,
        *,
        raw_points: Mapping[str, Point2D] | None = None,
    ) -> HandLandmarks | None:
        if detection.confidence < self.min_detection_confidence:
            return None

        return HandLandmarks(
            index_tip=_copy_point(detection.index_tip),
            thumb_tip=_copy_point(detection.thumb_tip),
            wrist=_copy_point(detection.wrist),
            middle_mcp=_copy_point(detection.middle_mcp),
            confidence=detection.confidence,
            raw_index_tip=_copy_raw_point(raw_points, "index_tip", detection.index_tip),
            raw_thumb_tip=_copy_raw_point(raw_points, "thumb_tip", detection.thumb_tip),
            raw_wrist=_copy_raw_point(raw_points, "wrist", detection.wrist),
            raw_middle_mcp=_copy_raw_point(raw_points, "middle_mcp", detection.middle_mcp),
        )

    def from_normalized_points(
        self,
        points: Mapping[str, object],
        confidence: float,
        *,
        field_map: Mapping[str, str] | None = None,
    ) -> HandLandmarks | None:
        detection = NormalizedHandDetection.from_normalized_points(
            points=points,
            confidence=confidence,
            field_map=field_map,
        )
        return self.from_detection(detection)


def _copy_point(point: Point2D) -> Point2D:
    return Point2D(x=point.x, y=point.y)


def _copy_raw_point(
    raw_points: Mapping[str, Point2D] | None,
    name: str,
    fallback: Point2D,
) -> Point2D:
    if raw_points is None or name not in raw_points:
        return _copy_point(fallback)
    return _copy_point(raw_points[name])


@dataclass
class LandmarkSmoother:
    alpha: float

    def __post_init__(self) -> None:
        if self.alpha < 0.0 or self.alpha > 1.0:
            raise ValueError("alpha must be between 0.0 and 1.0")
        self._previous_points: dict[str, Point2D] = {}

    def update(self, points: Mapping[str, Point2D]) -> dict[str, Point2D]:
        smoothed_points: dict[str, Point2D] = {}
        for name, point in points.items():
            previous = self._previous_points.get(name)
            if previous is None or isclose(self.alpha, 1.0):
                smoothed = point
            else:
                smoothed = Point2D(
                    x=(self.alpha * point.x) + ((1.0 - self.alpha) * previous.x),
                    y=(self.alpha * point.y) + ((1.0 - self.alpha) * previous.y),
                )
            smoothed_points[name] = smoothed

        self._previous_points = dict(smoothed_points)
        return smoothed_points

    def reset(self) -> None:
        self._previous_points = {}


class MediaPipeHandLandmarkProvider:
    def __init__(
        self,
        *,
        model_path: str,
        min_detection_confidence: float,
        min_tracking_confidence: float,
        landmark_smoothing: float,
    ) -> None:
        import mediapipe as mp
        from mediapipe.tasks.python import vision
        from mediapipe.tasks.python.core.base_options import BaseOptions

        self._mp = mp
        self._adapter = HandTrackerAdapter(
            min_detection_confidence=min_detection_confidence,
        )
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._hands = vision.HandLandmarker.create_from_options(options)
        self._timestamp_ms = 0
        self._landmark_smoother = LandmarkSmoother(alpha=landmark_smoothing)
        self._all_landmarks_smoother = LandmarkSmoother(alpha=landmark_smoothing)

    def __call__(self, frame) -> HandLandmarks | None:
        import cv2

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(
            image_format=self._mp.ImageFormat.SRGB,
            data=rgb_frame,
        )
        self._timestamp_ms += 1
        results = self._hands.detect_for_video(mp_image, self._timestamp_ms)
        if not results.hand_landmarks:
            return None

        hand_landmarks = results.hand_landmarks[0]
        points = {
            "index_tip": _landmark_to_point(hand_landmarks[8]),
            "thumb_tip": _landmark_to_point(hand_landmarks[4]),
            "wrist": _landmark_to_point(hand_landmarks[0]),
            "middle_mcp": _landmark_to_point(hand_landmarks[9]),
        }
        confidence = 1.0
        if results.handedness:
            confidence = float(results.handedness[0][0].score)

        smoothed_points = self._landmark_smoother.update(
            {
                "index_tip": Point2D(*points["index_tip"]),
                "thumb_tip": Point2D(*points["thumb_tip"]),
                "wrist": Point2D(*points["wrist"]),
                "middle_mcp": Point2D(*points["middle_mcp"]),
            }
        )
        adapted = self._adapter.from_normalized_points(
            {
                name: (point.x, point.y)
                for name, point in smoothed_points.items()
            },
            confidence,
        )
        if adapted is None:
            return None

        all_points = tuple(_landmark_to_point_object(point) for point in hand_landmarks)
        if all_points:
            smoothed_all_points_map = self._all_landmarks_smoother.update(
                {
                    f"all_{index}": point
                    for index, point in enumerate(all_points)
                }
            )
            smoothed_all_points = tuple(
                smoothed_all_points_map[f"all_{index}"] for index in range(len(all_points))
            )
        else:
            smoothed_all_points = ()

        return HandLandmarks(
            index_tip=adapted.index_tip,
            thumb_tip=adapted.thumb_tip,
            wrist=adapted.wrist,
            middle_mcp=adapted.middle_mcp,
            confidence=adapted.confidence,
            all_points=smoothed_all_points,
            raw_index_tip=Point2D(*points["index_tip"]),
            raw_thumb_tip=Point2D(*points["thumb_tip"]),
            raw_wrist=Point2D(*points["wrist"]),
            raw_middle_mcp=Point2D(*points["middle_mcp"]),
        )

    def close(self) -> None:
        self._landmark_smoother.reset()
        self._all_landmarks_smoother.reset()
        self._hands.close()


def _landmark_to_point(landmark) -> tuple[float, float]:
    return (float(landmark.x), float(landmark.y))


def _landmark_to_point_object(landmark) -> Point2D:
    return Point2D(x=float(landmark.x), y=float(landmark.y))
