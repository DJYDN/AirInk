from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from airwrite.interaction.gesture_state import GestureState
from airwrite.trajectory.stroke import Stroke, StrokePoint


class SessionPhase(str, Enum):
    IDLE = "IDLE"
    COLLECTING = "COLLECTING"
    PENDING_OCR = "PENDING_OCR"
    SHOWING_CANDIDATES = "SHOWING_CANDIDATES"


@dataclass
class WritingSession:
    strokes: list[Stroke] = field(default_factory=list)
    candidates: list[str] = field(default_factory=list)
    accepted_text: str = ""


@dataclass
class SessionController:
    ocr_idle_timeout_ms: float
    session: WritingSession = field(default_factory=WritingSession)
    phase: SessionPhase = field(default=SessionPhase.IDLE, init=False)
    active_stroke: Stroke | None = field(default=None, init=False)
    _last_pen_up_ms: float | None = field(default=None, init=False, repr=False)
    _last_gesture_state: GestureState = field(default=GestureState.FIST, init=False, repr=False)
    _pen_up_pending: bool = field(default=False, init=False, repr=False)

    def update_gesture(self, gesture_state: GestureState, *, timestamp_ms: float) -> None:
        if (
            gesture_state is GestureState.DRAWING
            and self._last_gesture_state is not GestureState.DRAWING
        ):
            self.on_pen_down()
        elif (
            gesture_state is GestureState.ARMING_UP
            and self._last_gesture_state is GestureState.DRAWING
        ):
            self._pen_up_pending = True
        elif (
            gesture_state in (GestureState.FIST, GestureState.HAND_LOST)
            and self._last_gesture_state in (GestureState.DRAWING, GestureState.ARMING_UP)
        ):
            self.on_pen_up(timestamp_ms=timestamp_ms)

        self._last_gesture_state = gesture_state

    def on_pen_down(self) -> None:
        if self.active_stroke is None:
            self.active_stroke = Stroke()
        self._pen_up_pending = False
        self.phase = SessionPhase.COLLECTING
        self.session.candidates = []

    def add_point(self, x: float, y: float, *, confidence: float, timestamp_ms: float) -> None:
        if self.active_stroke is None:
            self.active_stroke = Stroke()

        self.active_stroke.add_point(
            StrokePoint(x=x, y=y, t=timestamp_ms, confidence=confidence)
        )
        self.phase = SessionPhase.COLLECTING

    def on_pen_up(self, *, timestamp_ms: float) -> None:
        if self.active_stroke is not None and self.active_stroke.points:
            self.session.strokes.append(self.active_stroke)
        self.active_stroke = None
        self._pen_up_pending = False
        self._last_pen_up_ms = timestamp_ms
        if self.session.strokes:
            self.phase = SessionPhase.COLLECTING
        else:
            self.phase = SessionPhase.IDLE

    def split_active_stroke(self) -> None:
        if self.active_stroke is not None and self.active_stroke.points:
            self.session.strokes.append(self.active_stroke)
        self.active_stroke = Stroke()
        self._pen_up_pending = False
        self._last_pen_up_ms = None
        self.phase = SessionPhase.COLLECTING
        self.session.candidates = []

    def ready_for_ocr(self, *, timestamp_ms: float) -> bool:
        if self.phase is SessionPhase.SHOWING_CANDIDATES:
            return False
        if self.active_stroke is not None or not self.session.strokes or self._last_pen_up_ms is None:
            return False
        if timestamp_ms - self._last_pen_up_ms < self.ocr_idle_timeout_ms:
            return False

        self.phase = SessionPhase.PENDING_OCR
        return True

    def set_candidates(self, candidates: list[str]) -> None:
        self.session.candidates = list(candidates)
        self.phase = SessionPhase.SHOWING_CANDIDATES

    def confirm_candidate(self, candidate: str) -> str:
        self.session.accepted_text = candidate
        self.session.strokes = []
        self.session.candidates = []
        self.active_stroke = None
        self._last_pen_up_ms = None
        self.phase = SessionPhase.IDLE
        return candidate

    def clear(self) -> None:
        self.session = WritingSession()
        self.active_stroke = None
        self._pen_up_pending = False
        self._last_pen_up_ms = None
        self.phase = SessionPhase.IDLE

    def undo_last_stroke(self) -> Stroke | None:
        if self.active_stroke is not None and self.active_stroke.points:
            removed = self.active_stroke
            self.active_stroke = None
            return removed
        if not self.session.strokes:
            return None

        removed = self.session.strokes.pop()
        if not self.session.strokes:
            self.phase = SessionPhase.IDLE
        return removed
