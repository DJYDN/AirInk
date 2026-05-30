# AirWrite Handwriting Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the current pinch-drawing prototype into a handwriting-input workflow with stroke separation, gesture-gated pen up/down, session-level OCR candidates, and a top-row camera/skeleton/OCR layout.

**Architecture:** Split the input pipeline into `gesture classification -> stroke/session controller -> filtered stroke points -> session OCR candidates`. Keep UI panels explicit so camera, skeleton, session, and OCR state can be debugged independently. Reuse the current real-time camera loop, but stop treating the canvas as a flat list of points.

**Tech Stack:** Python 3.13, PySide6, NumPy, OpenCV, MediaPipe Tasks, pytest, pytest-qt

---

## File Structure

- `src/airwrite/config/defaults.py`: add handwriting-input defaults
- `src/airwrite/config/settings.py`: persist new tracking and session controls
- `src/airwrite/tracking/landmarks.py`: inspect points for gesture classification
- `src/airwrite/interaction/gesture_state.py`: new gesture classifier and state enums
- `src/airwrite/interaction/session_controller.py`: stroke/session lifecycle and OCR pending logic
- `src/airwrite/trajectory/filters.py`: replace passthrough-only behavior with deadzone-aware smoothing
- `src/airwrite/trajectory/stroke.py`: move from flat point list to stroke/session models
- `src/airwrite/ui/canvas_widget.py`: render independent strokes and session data
- `src/airwrite/ui/camera_preview.py`: reuse for raw camera and skeleton panels
- `src/airwrite/ui/ocr_panel.py`: new candidate/status widget
- `src/airwrite/ui/main_window.py`: top three panels + bottom canvas
- `src/airwrite/ui/status_bar.py`: show gesture/session state in addition to metrics
- `src/airwrite/app.py`: wire the new controller, skeleton overlay, session OCR trigger, and candidate confirmation
- `tests/unit/test_gesture_state.py`: gesture transition gating tests
- `tests/unit/test_session_controller.py`: stroke/session/OCR lifecycle tests
- `tests/unit/test_filters.py`: deadzone and reset tests
- `tests/unit/test_canvas_widget.py`: multi-stroke rendering tests
- `tests/integration/test_handwriting_input_session.py`: app-level session behavior

### Task 1: Add gesture and session domain models

**Files:**
- Create: `src/airwrite/interaction/gesture_state.py`
- Create: `src/airwrite/interaction/session_controller.py`
- Modify: `src/airwrite/trajectory/stroke.py`
- Test: `tests/unit/test_gesture_state.py`
- Test: `tests/unit/test_session_controller.py`

- [ ] **Step 1: Write failing tests for pen-down and pen-up gating**

```python
from airwrite.interaction.gesture_state import GestureClassifier, GestureState


def test_classifier_requires_stable_extension_before_drawing():
    classifier = GestureClassifier(stable_frames=2)

    assert classifier.update(is_index_extended=False) is GestureState.FIST
    assert classifier.update(is_index_extended=True) is GestureState.ARMING_DOWN
    assert classifier.update(is_index_extended=True) is GestureState.DRAWING
```

```python
from airwrite.interaction.session_controller import SessionController, SessionPhase


def test_session_controller_ends_stroke_without_triggering_ocr_immediately():
    controller = SessionController(ocr_idle_timeout_ms=300)
    controller.on_pen_down()
    controller.add_point(10, 10, confidence=0.9, timestamp_ms=0.0)
    controller.on_pen_up(timestamp_ms=100.0)

    assert len(controller.session.strokes) == 1
    assert controller.phase is SessionPhase.COLLECTING
```

- [ ] **Step 2: Run the targeted tests and verify RED**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_gesture_state.py tests/unit/test_session_controller.py -v`

Expected: import errors for the new controller modules

- [ ] **Step 3: Implement the minimal enums and controller types**

```python
class GestureState(str, Enum):
    FIST = "FIST"
    ARMING_DOWN = "ARMING_DOWN"
    DRAWING = "DRAWING"
    ARMING_UP = "ARMING_UP"
    HAND_LOST = "HAND_LOST"
```

```python
@dataclass
class WritingSession:
    strokes: list[Stroke] = field(default_factory=list)
    candidates: list[str] = field(default_factory=list)
```

- [ ] **Step 4: Re-run the targeted tests and verify GREEN**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_gesture_state.py tests/unit/test_session_controller.py -v`

Expected: targeted unit tests pass

### Task 2: Replace flat-point drawing with filtered multi-stroke drawing

**Files:**
- Modify: `src/airwrite/trajectory/filters.py`
- Modify: `src/airwrite/ui/canvas_widget.py`
- Test: `tests/unit/test_filters.py`
- Test: `tests/unit/test_canvas_widget.py`

- [ ] **Step 1: Write failing tests for deadzone suppression and stroke-separated rendering**

```python
def test_deadzone_filter_suppresses_micro_jitter():
    point_filter = DeadzoneFilter(deadzone=3.0)
    first = point_filter.update(StrokePoint(x=10.0, y=10.0, t=0.0, confidence=1.0))
    second = point_filter.update(StrokePoint(x=11.0, y=10.5, t=1.0, confidence=1.0))

    assert first is not None
    assert second is None
```

```python
def test_canvas_widget_does_not_connect_separate_strokes():
    widget = CanvasWidget()
    widget.set_strokes([
        Stroke(points=[StrokePoint(10, 10, 0.0, 1.0), StrokePoint(40, 10, 1.0, 1.0)]),
        Stroke(points=[StrokePoint(10, 40, 2.0, 1.0), StrokePoint(40, 40, 3.0, 1.0)]),
    ])

    assert len(widget.strokes) == 2
```

- [ ] **Step 2: Run the targeted tests and verify RED**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_filters.py tests/unit/test_canvas_widget.py -v`

Expected: missing filter behavior and canvas session API

- [ ] **Step 3: Implement minimal deadzone-aware filtering and stroke rendering**

```python
class DeadzoneFilter:
    def __init__(self, deadzone: float) -> None:
        self.deadzone = deadzone
        self._last_emitted: StrokePoint | None = None
```

```python
class CanvasWidget(QWidget):
    def set_strokes(self, strokes: list[Stroke]) -> None:
        self.strokes = strokes
        self.update()
```

- [ ] **Step 4: Re-run the targeted tests and verify GREEN**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_filters.py tests/unit/test_canvas_widget.py -v`

Expected: targeted rendering/filter tests pass

### Task 3: Add OCR panel and top-row debugging layout

**Files:**
- Create: `src/airwrite/ui/ocr_panel.py`
- Modify: `src/airwrite/ui/main_window.py`
- Modify: `src/airwrite/ui/status_bar.py`
- Test: `tests/integration/test_main_window_smoke.py`

- [ ] **Step 1: Write a failing UI smoke test for the three top panels**

```python
def test_main_window_exposes_camera_skeleton_and_ocr_panels(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.camera_preview is not None
    assert window.skeleton_preview is not None
    assert window.ocr_panel is not None
```

- [ ] **Step 2: Run the UI smoke test and verify RED**

Run: `.\.venv\Scripts\python -m pytest tests/integration/test_main_window_smoke.py -v`

Expected: missing skeleton/OCR panel attributes

- [ ] **Step 3: Implement the layout and OCR candidate widget**

```python
class OcrPanel(QWidget):
    def set_candidates(self, candidates: list[str]) -> None:
        ...
```

```python
self.camera_preview = CameraPreviewWidget(title="Camera")
self.skeleton_preview = CameraPreviewWidget(title="Skeleton")
self.ocr_panel = OcrPanel()
```

- [ ] **Step 4: Re-run the UI smoke test and verify GREEN**

Run: `.\.venv\Scripts\python -m pytest tests/integration/test_main_window_smoke.py -v`

Expected: top-row layout test passes

### Task 4: Wire the real-time app loop to gesture/session/OCR flow

**Files:**
- Modify: `src/airwrite/app.py`
- Modify: `src/airwrite/tracking/hand_tracker.py`
- Modify: `src/airwrite/config/defaults.py`
- Modify: `src/airwrite/config/settings.py`
- Test: `tests/integration/test_handwriting_input_session.py`
- Test: `tests/unit/test_settings_persistence_ui.py`

- [ ] **Step 1: Write a failing app-level session test**

```python
def test_app_collects_multiple_strokes_then_shows_ocr_candidates(tmp_path, monkeypatch, qtbot):
    app = AirWriteApp.for_test(...)
    # drive gesture states: fist -> extended -> fist -> extended -> fist
    # then wait past idle timeout
    assert app.window.ocr_panel.candidates() == ["candidate-1"]
```

- [ ] **Step 2: Run the app-level tests and verify RED**

Run: `.\.venv\Scripts\python -m pytest tests/integration/test_handwriting_input_session.py tests/unit/test_settings_persistence_ui.py -v`

Expected: app still uses flat points and has no session OCR flow

- [ ] **Step 3: Implement the minimal session OCR pipeline**

```python
gesture_state = self._gesture_classifier.update(...)
session_event = self._session_controller.update(...)
```

```python
if self._session_controller.ready_for_ocr(now_ms):
    self.window.ocr_panel.set_candidates(self._ocr_provider.recognize(session_image))
```

- [ ] **Step 4: Re-run the app-level tests and verify GREEN**

Run: `.\.venv\Scripts\python -m pytest tests/integration/test_handwriting_input_session.py tests/unit/test_settings_persistence_ui.py -v`

Expected: session tests pass and the new settings round-trip correctly

### Task 5: Full verification

**Files:**
- Verify existing and new tests

- [ ] **Step 1: Run focused unit and integration tests**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_gesture_state.py tests/unit/test_session_controller.py tests/unit/test_filters.py tests/unit/test_canvas_widget.py tests/integration/test_handwriting_input_session.py tests/integration/test_main_window_smoke.py -v`

Expected: all targeted tests pass

- [ ] **Step 2: Run broader verification**

Run: `.\.venv\Scripts\python -m pytest tests/unit tests/integration tests/packaging -v`

Expected: no regressions across the existing suite

- [ ] **Step 3: Launch the app for manual validation**

Run: `powershell -ExecutionPolicy Bypass -File scripts/run_app.ps1`

Expected:

- top row shows camera, skeleton, and OCR
- bottom canvas accumulates multiple strokes
- pen transitions do not generate transition scribbles
- OCR candidates remain visible until confirmation

## Self-Review

**Spec coverage**

- gesture-driven pen-up and pen-down are covered by Task 1 and Task 4
- transition no-ink handling is covered by Task 1 and Task 4
- multi-stroke session behavior is covered by Task 1, Task 2, and Task 4
- top-row camera/skeleton/OCR layout is covered by Task 3
- session-level OCR candidates and confirmation flow are covered by Task 4

**Placeholder scan**

- no `TODO` or `TBD` placeholders remain
- each task lists exact files and concrete test commands

**Type consistency**

- `GestureState`, `SessionController`, `WritingSession`, `Stroke`, `CanvasWidget`, and `OcrPanel` are used consistently across tasks
