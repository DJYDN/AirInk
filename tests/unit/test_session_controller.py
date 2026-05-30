from airwrite.interaction.gesture_state import GestureState
from airwrite.interaction.session_controller import SessionController, SessionPhase


def test_session_controller_creates_distinct_strokes_across_pen_cycles() -> None:
    controller = SessionController(ocr_idle_timeout_ms=300.0)

    controller.update_gesture(GestureState.DRAWING, timestamp_ms=0.0)
    controller.add_point(10.0, 20.0, confidence=0.9, timestamp_ms=1.0)
    controller.add_point(20.0, 30.0, confidence=0.9, timestamp_ms=2.0)
    controller.update_gesture(GestureState.FIST, timestamp_ms=3.0)
    controller.update_gesture(GestureState.DRAWING, timestamp_ms=4.0)
    controller.add_point(40.0, 50.0, confidence=0.9, timestamp_ms=5.0)
    controller.update_gesture(GestureState.FIST, timestamp_ms=6.0)

    assert len(controller.session.strokes) == 2
    assert [len(stroke.points) for stroke in controller.session.strokes] == [2, 1]
    assert controller.phase is SessionPhase.COLLECTING


def test_session_controller_only_becomes_pending_after_idle_timeout() -> None:
    controller = SessionController(ocr_idle_timeout_ms=300.0)

    controller.update_gesture(GestureState.DRAWING, timestamp_ms=0.0)
    controller.add_point(10.0, 20.0, confidence=0.9, timestamp_ms=1.0)
    controller.update_gesture(GestureState.FIST, timestamp_ms=2.0)

    assert controller.ready_for_ocr(timestamp_ms=250.0) is False
    assert controller.phase is SessionPhase.COLLECTING
    assert controller.ready_for_ocr(timestamp_ms=350.0) is True
    assert controller.phase is SessionPhase.PENDING_OCR


def test_session_controller_keeps_candidates_until_confirmation() -> None:
    controller = SessionController(ocr_idle_timeout_ms=300.0)

    controller.update_gesture(GestureState.DRAWING, timestamp_ms=0.0)
    controller.add_point(10.0, 20.0, confidence=0.9, timestamp_ms=1.0)
    controller.update_gesture(GestureState.FIST, timestamp_ms=2.0)
    controller.ready_for_ocr(timestamp_ms=400.0)
    controller.set_candidates(["hello", "hullo"])

    assert controller.phase is SessionPhase.SHOWING_CANDIDATES
    assert controller.session.candidates == ["hello", "hullo"]

    selected = controller.confirm_candidate("hello")

    assert selected == "hello"
    assert controller.phase is SessionPhase.IDLE
    assert controller.session.strokes == []
    assert controller.session.candidates == []


def test_session_controller_keeps_active_stroke_open_when_gesture_enters_arming_up() -> None:
    controller = SessionController(ocr_idle_timeout_ms=300.0)

    controller.update_gesture(GestureState.DRAWING, timestamp_ms=0.0)
    controller.add_point(10.0, 20.0, confidence=0.9, timestamp_ms=1.0)
    controller.update_gesture(GestureState.ARMING_UP, timestamp_ms=2.0)

    assert len(controller.session.strokes) == 0
    assert controller.active_stroke is not None
    assert controller.phase is SessionPhase.COLLECTING


def test_session_controller_closes_pending_stroke_when_fist_follows_arming_up() -> None:
    controller = SessionController(ocr_idle_timeout_ms=300.0)

    controller.update_gesture(GestureState.DRAWING, timestamp_ms=0.0)
    controller.add_point(10.0, 20.0, confidence=0.9, timestamp_ms=1.0)
    controller.update_gesture(GestureState.ARMING_UP, timestamp_ms=2.0)
    controller.update_gesture(GestureState.FIST, timestamp_ms=3.0)

    assert len(controller.session.strokes) == 1
    assert controller.active_stroke is None


def test_session_controller_resumes_same_stroke_when_drawing_returns_after_arming_up() -> None:
    controller = SessionController(ocr_idle_timeout_ms=300.0)

    controller.update_gesture(GestureState.DRAWING, timestamp_ms=0.0)
    controller.add_point(10.0, 20.0, confidence=0.9, timestamp_ms=1.0)
    controller.update_gesture(GestureState.ARMING_UP, timestamp_ms=2.0)
    controller.update_gesture(GestureState.DRAWING, timestamp_ms=3.0)
    controller.add_point(14.0, 24.0, confidence=0.9, timestamp_ms=4.0)
    controller.update_gesture(GestureState.FIST, timestamp_ms=5.0)

    assert len(controller.session.strokes) == 1
    assert [point.x for point in controller.session.strokes[0].points] == [10.0, 14.0]
