from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DrawingState(str, Enum):
    NO_HAND = "NO_HAND"
    HOVER = "HOVER"
    DRAWING = "DRAWING"
    LOST = "LOST"


@dataclass
class DrawingStateMachine:
    lost_frame_limit: int = 1
    state: DrawingState = field(default=DrawingState.NO_HAND, init=False)
    _lost_frames: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.lost_frame_limit < 1:
            raise ValueError("lost_frame_limit must be at least 1")

    def on_hand_detected(self, *, is_drawing: bool) -> DrawingState:
        self._lost_frames = 0
        self.state = DrawingState.DRAWING if is_drawing else DrawingState.HOVER
        return self.state

    def on_no_hand(self) -> DrawingState:
        if self.state is DrawingState.NO_HAND:
            return self.state

        self._lost_frames += 1
        if self._lost_frames >= self.lost_frame_limit:
            self.state = DrawingState.NO_HAND
            self._lost_frames = 0
        else:
            self.state = DrawingState.LOST

        return self.state
