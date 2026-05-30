from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from airwrite.tracking.landmarks import HandLandmarks
from airwrite.tracking.pen_pose import PenPose, derive_pen_pose


class GestureState(str, Enum):
    FIST = "FIST"
    ARMING_DOWN = "ARMING_DOWN"
    DRAWING = "DRAWING"
    ARMING_UP = "ARMING_UP"
    HAND_LOST = "HAND_LOST"


@dataclass
class GestureClassifier:
    stable_frames: int
    fist_ratio_threshold: float
    extended_ratio_threshold: float
    hand_loss_grace_frames: int = 0
    pinch_down_threshold: float = 0.30
    pinch_up_threshold: float = 0.45
    pen_up_stable_frames: int | None = None
    _stable_posture: str = field(default="fist", init=False, repr=False)
    _pending_posture: str | None = field(default=None, init=False, repr=False)
    _pending_frames: int = field(default=0, init=False, repr=False)
    _missing_frames: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.stable_frames < 1:
            raise ValueError("stable_frames must be at least 1")
        if self.hand_loss_grace_frames < 0:
            raise ValueError("hand_loss_grace_frames must be non-negative")
        if self.fist_ratio_threshold < 0.0 or self.extended_ratio_threshold < 0.0:
            raise ValueError("gesture thresholds must be non-negative")
        if self.fist_ratio_threshold > self.extended_ratio_threshold:
            raise ValueError("fist_ratio_threshold must be <= extended_ratio_threshold")
        if self.pinch_down_threshold <= 0.0 or self.pinch_up_threshold <= 0.0:
            raise ValueError("pinch thresholds must be positive")
        if self.pinch_down_threshold >= self.pinch_up_threshold:
            raise ValueError("pinch_down_threshold must be smaller than pinch_up_threshold")
        if self.pen_up_stable_frames is None:
            self.pen_up_stable_frames = max(self.stable_frames, 4)
        if self.pen_up_stable_frames < 1:
            raise ValueError("pen_up_stable_frames must be at least 1")

    def update(self, landmarks_or_pose: HandLandmarks | PenPose | None) -> GestureState:
        if landmarks_or_pose is None:
            self._pending_posture = None
            self._pending_frames = 0
            self._missing_frames += 1
            if self._missing_frames <= self.hand_loss_grace_frames:
                return self._state_for_posture(self._stable_posture)
            return GestureState.HAND_LOST

        self._missing_frames = 0
        pose = self._coerce_pose(landmarks_or_pose)
        posture = self._classify_pose(pose)
        if posture == "hold":
            self._pending_posture = None
            self._pending_frames = 0
            return self._state_for_posture(self._stable_posture)

        if posture == self._stable_posture:
            self._pending_posture = None
            self._pending_frames = 0
            return self._state_for_posture(self._stable_posture)

        return self._advance_pending_posture(posture)

    def _classify_pose(self, pose: PenPose) -> str:
        pinch_posture = self._classify_pinch(pose.pinch_ratio)
        if pinch_posture != "unknown":
            return pinch_posture
        return self._classify_extension(pose.extension_ratio)

    def _classify_pinch(self, pinch_ratio: float | None) -> str:
        if pinch_ratio is None:
            return "unknown"
        if pinch_ratio <= self.pinch_down_threshold:
            return "extended"
        if pinch_ratio >= self.pinch_up_threshold:
            return "fist"
        return "hold"

    def _classify_extension(self, extension_ratio: float) -> str:
        if extension_ratio <= self.fist_ratio_threshold:
            return "fist"
        if extension_ratio >= self.extended_ratio_threshold:
            return "extended"
        return "hold"

    def _coerce_pose(self, landmarks_or_pose: HandLandmarks | PenPose) -> PenPose:
        if isinstance(landmarks_or_pose, PenPose):
            return landmarks_or_pose
        return derive_pen_pose(landmarks_or_pose)

    def _advance_pending_posture(self, posture: str) -> GestureState:
        if self._pending_posture != posture:
            self._pending_posture = posture
            self._pending_frames = 1
        else:
            self._pending_frames += 1

        required_frames = self.pen_up_stable_frames if posture == "fist" else self.stable_frames
        if self._pending_frames >= required_frames:
            self._stable_posture = posture
            self._pending_posture = None
            self._pending_frames = 0
            return self._state_for_posture(posture)

        return self._arming_state(posture)

    @staticmethod
    def _state_for_posture(posture: str) -> GestureState:
        return GestureState.DRAWING if posture == "extended" else GestureState.FIST

    @staticmethod
    def _arming_state(target_posture: str) -> GestureState:
        return GestureState.ARMING_DOWN if target_posture == "extended" else GestureState.ARMING_UP
