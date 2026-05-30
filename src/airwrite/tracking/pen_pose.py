from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from airwrite.tracking.landmarks import HandLandmarks, Point2D

_INDEX_MCP = 5
_INDEX_PIP = 6
_INDEX_DIP = 7
_INDEX_TIP = 8


@dataclass(frozen=True)
class PenPose:
    tip: Point2D
    raw_tip: Point2D
    source: str
    extension_ratio: float
    confidence: float
    pinch_ratio: float | None = None


@dataclass
class PenPoseSmoother:
    alpha: float

    def __post_init__(self) -> None:
        if self.alpha < 0.0 or self.alpha > 1.0:
            raise ValueError("alpha must be between 0.0 and 1.0")
        self._previous_pose: PenPose | None = None

    def update(self, pose: PenPose) -> PenPose:
        previous = self._previous_pose
        if previous is None or self.alpha >= 1.0:
            self._previous_pose = pose
            return pose

        smoothed = PenPose(
            tip=_smooth_point(previous.tip, pose.tip, alpha=self.alpha),
            raw_tip=_smooth_point(previous.raw_tip, pose.raw_tip, alpha=self.alpha),
            source=pose.source,
            extension_ratio=(self.alpha * pose.extension_ratio)
            + ((1.0 - self.alpha) * previous.extension_ratio),
            confidence=pose.confidence,
            pinch_ratio=_smooth_optional_number(previous.pinch_ratio, pose.pinch_ratio, alpha=self.alpha),
        )
        self._previous_pose = smoothed
        return smoothed

    def reset(self) -> None:
        self._previous_pose = None


def derive_pen_pose(landmarks: HandLandmarks) -> PenPose:
    tip, source = _resolve_tip(landmarks)
    extension_ratio = _resolve_extension_ratio(landmarks)

    return PenPose(
        tip=tip,
        raw_tip=landmarks.raw_index_tip,
        source=source,
        extension_ratio=extension_ratio,
        confidence=landmarks.confidence,
        pinch_ratio=_resolve_pinch_ratio(landmarks),
    )


def _resolve_tip(landmarks: HandLandmarks) -> tuple[Point2D, str]:
    if len(landmarks.all_points) > _INDEX_TIP:
        pip = landmarks.all_points[_INDEX_PIP]
        dip = landmarks.all_points[_INDEX_DIP]
        tip = landmarks.all_points[_INDEX_TIP]
        return (
            Point2D(
                x=(pip.x * 0.1) + (dip.x * 0.3) + (tip.x * 0.6),
                y=(pip.y * 0.1) + (dip.y * 0.3) + (tip.y * 0.6),
            ),
            "index_chain",
        )

    return (landmarks.index_tip, "index_tip")


def _resolve_extension_ratio(landmarks: HandLandmarks) -> float:
    if len(landmarks.all_points) > _INDEX_TIP:
        mcp = landmarks.all_points[_INDEX_MCP]
        pip = landmarks.all_points[_INDEX_PIP]
        dip = landmarks.all_points[_INDEX_DIP]
        tip = landmarks.all_points[_INDEX_TIP]
        direct = _distance(mcp, tip)
        chain = _distance(mcp, pip) + _distance(pip, dip) + _distance(dip, tip)
        if chain > 0.0:
            return direct / chain

    hand_scale = hypot(
        landmarks.middle_mcp.x - landmarks.wrist.x,
        landmarks.middle_mcp.y - landmarks.wrist.y,
    )
    if hand_scale == 0.0:
        return 0.0

    return hypot(
        landmarks.index_tip.x - landmarks.wrist.x,
        landmarks.index_tip.y - landmarks.wrist.y,
    ) / hand_scale


def _resolve_pinch_ratio(landmarks: HandLandmarks) -> float | None:
    hand_scale = _distance(landmarks.wrist, landmarks.middle_mcp)
    if hand_scale <= 0.0:
        return None
    return _distance(landmarks.thumb_tip, landmarks.index_tip) / hand_scale


def _distance(start: Point2D, end: Point2D) -> float:
    return hypot(end.x - start.x, end.y - start.y)


def _smooth_point(previous: Point2D, current: Point2D, *, alpha: float) -> Point2D:
    return Point2D(
        x=(alpha * current.x) + ((1.0 - alpha) * previous.x),
        y=(alpha * current.y) + ((1.0 - alpha) * previous.y),
    )


def _smooth_optional_number(previous: float | None, current: float | None, *, alpha: float) -> float | None:
    if previous is None or current is None:
        return current
    return (alpha * current) + ((1.0 - alpha) * previous)
