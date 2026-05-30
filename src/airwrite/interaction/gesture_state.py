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

    def update(self, landmarks_or_pose: HandLandmarks | PenPose | None) -> GestureState:
        if landmarks_or_pose is None:
            self._pending_posture = None
            self._pending_frames = 0
            self._missing_frames += 1
            if self._missing_frames <= self.hand_loss_grace_frames:
                return self._state_for_posture(self._stable_posture)
            return GestureState.HAND_LOST

        self._missing_frames = 0

        posture = self._classify_posture(self._coerce_pose(landmarks_or_pose).extension_ratio)
        if posture == "transition":
            return (
                GestureState.ARMING_UP
                if self._stable_posture == "extended"
                else GestureState.ARMING_DOWN
            )

        if posture == self._stable_posture:
            self._pending_posture = None
            self._pending_frames = 0
            return self._state_for_posture(self._stable_posture)

        return self._advance_pending_posture(posture)

    def _classify_posture(self, extension_ratio: float) -> str:
        if extension_ratio <= self.fist_ratio_threshold:
            return "fist"
        if extension_ratio >= self.extended_ratio_threshold:
            return "extended"
        return "transition"

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

        if self._pending_frames >= self.stable_frames:
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
