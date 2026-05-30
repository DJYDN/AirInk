# AirWrite Interaction Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor AirWrite's live handwriting loop so writing becomes steadier, less jittery, and less prone to unintended stroke breaks while keeping the current session-based OCR workflow.

**Architecture:** Keep the current PySide app, MediaPipe provider, and multi-stroke session model, but split the interaction pipeline into explicit stages: smoothed hand landmarks, pen-pose derivation, intent gating, stroke stabilization, and calibrated mapping. Borrow `aircanvas` ideas at the tracking and draw-start levels without regressing AirWrite's session/OCR architecture.

**Tech Stack:** Python 3.13, PySide6, NumPy, OpenCV, MediaPipe Tasks, pytest, pytest-qt

---

## File Structure

- `src/airwrite/tracking/hand_tracker.py`: keep MediaPipe integration, but return richer and more stable landmark data
- `src/airwrite/tracking/landmarks.py`: extend typed hand data for pen-pose derivation and debug overlays
- `src/airwrite/tracking/pen_pose.py`: new pen-pose model derived from multiple finger joints
- `src/airwrite/interaction/gesture_state.py`: upgrade gesture classifier into handwriting-intent gating with hysteresis
- `src/airwrite/interaction/session_controller.py`: keep stroke/session lifecycle, but cooperate with the new stroke-stabilization signals
- `src/airwrite/trajectory/filters.py`: keep reusable point filters, but split start-anchor and continuity logic from raw smoothing
- `src/airwrite/trajectory/mapping.py`: support configurable writing-zone mapping and clamping
- `src/airwrite/app.py`: orchestrate the new pipeline stages and debug outputs
- `src/airwrite/ui/camera_preview.py`: support overlay labels for raw tip, stable tip, and writing zone
- `src/airwrite/ui/settings_panel.py`: expose the new interaction parameters
- `src/airwrite/config/defaults.py`: add defaults for the new handwriting controls
- `src/airwrite/config/settings.py`: validate and persist those controls
- `tests/unit/test_hand_tracker_mapping.py`: extend tracking and smoothing coverage
- `tests/unit/test_gesture_state.py`: extend intent gating coverage
- `tests/unit/test_filters.py`: add start-anchor and continuity tests
- `tests/unit/test_mapping.py`: add writing-zone tests
- `tests/unit/test_settings_persistence_ui.py`: extend settings coverage
- `tests/integration/test_handwriting_input_session.py`: cover app-level continuity and transition suppression

### Task 1: Introduce a typed pen-pose stage

**Files:**
- Create: `src/airwrite/tracking/pen_pose.py`
- Modify: `src/airwrite/tracking/landmarks.py`
- Modify: `src/airwrite/tracking/hand_tracker.py`
- Test: `tests/unit/test_hand_tracker_mapping.py`

- [ ] **Step 1: Write failing tests for stable pen-pose derivation**

```python
from airwrite.tracking.landmarks import HandLandmarks, Point2D
from airwrite.tracking.pen_pose import derive_pen_pose


def test_derive_pen_pose_uses_multiple_index_joints():
    landmarks = HandLandmarks(
        index_tip=Point2D(0.60, 0.20),
        thumb_tip=Point2D(0.48, 0.52),
        wrist=Point2D(0.50, 0.82),
        middle_mcp=Point2D(0.52, 0.60),
        confidence=0.95,
        all_points=(
            Point2D(0.50, 0.82),
            Point2D(0.48, 0.76),
            Point2D(0.47, 0.68),
            Point2D(0.46, 0.58),
            Point2D(0.46, 0.50),
            Point2D(0.54, 0.62),
            Point2D(0.57, 0.46),
            Point2D(0.59, 0.31),
            Point2D(0.60, 0.20),
        ),
    )

    pose = derive_pen_pose(landmarks)

    assert round(pose.tip.x, 3) == 0.593
    assert round(pose.tip.y, 3) == 0.281
    assert pose.source == "index_chain"
```

```python
import numpy as np
from airwrite.tracking.landmarks import Point2D


def test_provider_keeps_raw_and_smoothed_positions_for_debugging():
    provider = StubLandmarkProvider(
        outputs=[
            make_landmarks(index_tip=(0.40, 0.30)),
            make_landmarks(index_tip=(0.60, 0.30)),
        ],
        landmark_smoothing=0.5,
    )
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    first = provider(frame)
    second = provider(frame)

    assert first.raw_index_tip == Point2D(0.40, 0.30)
    assert second.raw_index_tip == Point2D(0.60, 0.30)
    assert second.index_tip.x < second.raw_index_tip.x
```

- [ ] **Step 2: Run the targeted tests and verify RED**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_hand_tracker_mapping.py -v`
Expected: import failure for `airwrite.tracking.pen_pose` or missing `raw_index_tip` / pose fields

- [ ] **Step 3: Implement the minimal pen-pose types and provider plumbing**

```python
@dataclass(frozen=True)
class PenPose:
    tip: Point2D
    raw_tip: Point2D
    source: str
    extension_ratio: float
    confidence: float
```

```python
def derive_pen_pose(landmarks: HandLandmarks) -> PenPose:
    tip = _weighted_index_chain_tip(landmarks)
    return PenPose(
        tip=tip,
        raw_tip=landmarks.index_tip,
        source="index_chain",
        extension_ratio=_compute_extension_ratio(landmarks),
        confidence=landmarks.confidence,
    )
```

- [ ] **Step 4: Re-run the targeted tests and verify GREEN**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_hand_tracker_mapping.py -v`
Expected: pen-pose derivation and debug-point tests pass

### Task 2: Upgrade gesture classification into intent gating

**Files:**
- Modify: `src/airwrite/interaction/gesture_state.py`
- Modify: `src/airwrite/tracking/pen_pose.py`
- Test: `tests/unit/test_gesture_state.py`

- [ ] **Step 1: Write failing tests for handwriting-intent hysteresis**

```python
from airwrite.interaction.gesture_state import GestureClassifier, GestureState
from airwrite.tracking.pen_pose import PenPose
from airwrite.tracking.landmarks import Point2D


def make_pose(extension_ratio: float) -> PenPose:
    return PenPose(
        tip=Point2D(0.5, 0.3),
        raw_tip=Point2D(0.5, 0.3),
        source="index_chain",
        extension_ratio=extension_ratio,
        confidence=0.95,
    )


def test_classifier_requires_stable_frames_before_entering_drawing():
    classifier = GestureClassifier(
        stable_frames=3,
        fist_ratio_threshold=0.9,
        extended_ratio_threshold=1.4,
        hand_loss_grace_frames=4,
    )

    assert classifier.update(make_pose(0.8)) is GestureState.FIST
    assert classifier.update(make_pose(1.2)) is GestureState.ARMING_DOWN
    assert classifier.update(make_pose(1.45)) is GestureState.ARMING_DOWN
    assert classifier.update(make_pose(1.46)) is GestureState.DRAWING
```

```python
def test_classifier_holds_drawing_through_brief_uncertain_frames():
    classifier = GestureClassifier(
        stable_frames=2,
        fist_ratio_threshold=0.9,
        extended_ratio_threshold=1.4,
        hand_loss_grace_frames=3,
    )

    classifier.update(make_pose(0.8))
    classifier.update(make_pose(1.45))
    assert classifier.update(make_pose(1.50)) is GestureState.DRAWING
    assert classifier.update(make_pose(1.15)) is GestureState.DRAWING
```

- [ ] **Step 2: Run the targeted tests and verify RED**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_gesture_state.py -v`
Expected: current classifier only accepts `HandLandmarks` and does not hold uncertain frames as drawing

- [ ] **Step 3: Implement intent gating around pen pose instead of raw landmarks**

```python
def update(self, pose: PenPose | None) -> GestureState:
    if pose is None:
        return self._handle_missing_pose()

    posture = self._classify_posture(pose.extension_ratio)
    if posture == self._stable_posture:
        self._pending_posture = None
        self._pending_frames = 0
        return self._state_for_posture(self._stable_posture)

    return self._advance_pending_posture(posture)
```

```python
if posture == "transition" and self._stable_posture == "extended":
    return GestureState.DRAWING
```

- [ ] **Step 4: Re-run the targeted tests and verify GREEN**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_gesture_state.py -v`
Expected: intent gating tests pass with stable draw-entry and uncertain-frame hysteresis

### Task 3: Add stroke-stabilization and plausible dropout bridging

**Files:**
- Modify: `src/airwrite/trajectory/filters.py`
- Modify: `src/airwrite/app.py`
- Modify: `src/airwrite/interaction/session_controller.py`
- Test: `tests/unit/test_filters.py`
- Test: `tests/integration/test_handwriting_input_session.py`

- [ ] **Step 1: Write failing tests for start-anchor logic and plausible recovery**

```python
from airwrite.trajectory.filters import DeadzoneFilter
from airwrite.trajectory.stroke import StrokePoint


def test_filter_requires_anchor_then_real_movement_before_ink():
    point_filter = DeadzoneFilter(
        deadzone=4.0,
        smoothing=0.35,
        start_threshold=14.0,
        max_jump_distance=120.0,
    )

    assert point_filter.apply(StrokePoint(100.0, 100.0, 0.0, 0.9)) is None
    assert point_filter.apply(StrokePoint(108.0, 102.0, 1.0, 0.9)) is None
    assert point_filter.apply(StrokePoint(118.0, 106.0, 2.0, 0.9)) is not None
```

```python
from airwrite.app import AirWriteApp
from tests.integration.test_handwriting_input_session import SequenceLandmarkProvider, make_landmarks


def test_app_keeps_single_stroke_across_plausible_brief_dropout(qtbot):
    provider = SequenceLandmarkProvider(
        [
            make_landmarks(index_tip=(0.42, 0.30)),
            make_landmarks(index_tip=(0.44, 0.31)),
            None,
            make_landmarks(index_tip=(0.45, 0.32)),
        ]
    )
    app = AirWriteApp.for_test(hand_landmark_provider=provider)
    qtbot.addWidget(app.window)

    for _ in range(4):
        app._process_frame()

    assert len(app._session_controller.session.strokes) == 1
    assert len(app._session_controller.session.strokes[0].points) >= 2
```

- [ ] **Step 2: Run the targeted tests and verify RED**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_filters.py tests/integration/test_handwriting_input_session.py -v`
Expected: current filter and app loop do not model plausible recovery explicitly

- [ ] **Step 3: Implement stroke-local anchor, continuity, and recovery rules**

```python
class DeadzoneFilter:
    def can_recover_to(self, point: StrokePoint) -> bool:
        if self._last_emitted is None or self.max_jump_distance is None:
            return False
        return _distance(self._last_emitted, point) <= self.max_jump_distance
```

```python
if pose is None and self._session_controller.active_stroke is not None:
    self._continuity_state.mark_gap(timestamp_ms)
elif recovered_point is not None and self._continuity_state.can_resume_with(recovered_point):
    self._session_controller.add_point(
        recovered_point.x,
        recovered_point.y,
        confidence=recovered_point.confidence,
        timestamp_ms=recovered_point.t,
    )
```

- [ ] **Step 4: Re-run the targeted tests and verify GREEN**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_filters.py tests/integration/test_handwriting_input_session.py -v`
Expected: no-ink-on-transition, anchor gating, and plausible dropout recovery tests pass

### Task 4: Replace fixed active-region mapping with configurable writing-zone mapping

**Files:**
- Modify: `src/airwrite/trajectory/mapping.py`
- Modify: `src/airwrite/app.py`
- Modify: `src/airwrite/ui/camera_preview.py`
- Test: `tests/unit/test_mapping.py`
- Test: `tests/integration/test_handwriting_input_session.py`

- [ ] **Step 1: Write failing tests for writing-zone clamping and overlay metadata**

```python
from airwrite.trajectory.mapping import map_image_to_canvas


def test_map_image_to_canvas_clamps_to_writing_zone():
    x, y = map_image_to_canvas(
        image_x=40.0,
        image_y=20.0,
        image_width=200.0,
        image_height=100.0,
        canvas_width=1000.0,
        canvas_height=500.0,
        active_region=(0.25, 0.75, 0.20, 0.80),
    )

    assert x == 0.0
    assert y == 0.0
```

```python
from airwrite.app import AirWriteApp
from tests.integration.test_handwriting_input_session import SequenceLandmarkProvider, make_landmarks


def test_skeleton_preview_receives_writing_zone_overlay(qtbot):
    provider = SequenceLandmarkProvider(
        [make_landmarks(index_tip=(0.45, 0.35), confidence=0.92)]
    )
    app = AirWriteApp.for_test(hand_landmark_provider=provider)
    qtbot.addWidget(app.window)
    app._process_frame()

    overlay = app.window.skeleton_preview.current_overlay()
    assert overlay.active_region == (0.20, 0.80, 0.18, 0.82)
```

- [ ] **Step 2: Run the targeted tests and verify RED**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_mapping.py tests/integration/test_handwriting_input_session.py -v`
Expected: preview overlay metadata is missing and mapping remains fixed/hard-coded

- [ ] **Step 3: Implement writing-zone settings and skeleton overlay plumbing**

```python
ACTIVE_REGION_DEFAULT = (0.20, 0.80, 0.18, 0.82)
```

```python
overlay = PreviewOverlay(
    gesture=gesture_state.value,
    active_region=self._active_region,
    raw_tip=pose.raw_tip if pose else None,
    stable_tip=pose.tip if pose else None,
)
```

- [ ] **Step 4: Re-run the targeted tests and verify GREEN**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_mapping.py tests/integration/test_handwriting_input_session.py -v`
Expected: writing-zone mapping and preview overlay tests pass

### Task 5: Persist the new interaction controls in settings UI

**Files:**
- Modify: `src/airwrite/config/defaults.py`
- Modify: `src/airwrite/config/settings.py`
- Modify: `src/airwrite/ui/settings_panel.py`
- Test: `tests/unit/test_settings_persistence_ui.py`

- [ ] **Step 1: Write failing settings round-trip tests**

```python
def test_settings_panel_round_trips_interaction_controls(qtbot):
    settings = AppSettings.defaults()
    panel = SettingsPanel()
    qtbot.addWidget(panel)
    panel.load_settings(settings)

    panel.min_tracking_confidence_spinbox.setValue(0.75)
    panel.gesture_stable_frames_spinbox.setValue(3)
    panel.deadzone_spinbox.setValue(5.5)

    updated = panel.current_settings()

    assert updated.tracking.min_tracking_confidence == 0.75
    assert updated.tracking.gesture_stable_frames == 3
    assert updated.filter.deadzone == 5.5
```

- [ ] **Step 2: Run the targeted test and verify RED**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_settings_persistence_ui.py -v`
Expected: new controls or dataclass fields do not exist yet

- [ ] **Step 3: Implement the missing config fields and settings widgets**

```python
"tracking": {
    "min_detection_confidence": 0.7,
    "min_tracking_confidence": 0.75,
    "landmark_smoothing": 0.55,
    "gesture_stable_frames": 3,
    "lost_frame_limit": 10,
}
```

```python
form.addRow("Tracking confidence", self.min_tracking_confidence_spinbox)
form.addRow("Gesture stable frames", self.gesture_stable_frames_spinbox)
form.addRow("Deadzone", self.deadzone_spinbox)
```

- [ ] **Step 4: Re-run the targeted test and verify GREEN**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_settings_persistence_ui.py -v`
Expected: settings UI and persistence tests pass

### Task 6: Full verification and manual handwriting QA

**Files:**
- Verify existing and new tests

- [ ] **Step 1: Run focused unit and integration coverage**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_hand_tracker_mapping.py tests/unit/test_gesture_state.py tests/unit/test_filters.py tests/unit/test_mapping.py tests/unit/test_settings_persistence_ui.py tests/integration/test_handwriting_input_session.py -v`
Expected: all targeted tests pass

- [ ] **Step 2: Run broader regression coverage**

Run: `.\.venv\Scripts\python -m pytest tests/unit tests/integration tests/packaging -v`
Expected: all tests reach PASS; if the known teardown hang remains, capture it as a separate issue without blocking acceptance of the handwriting changes

- [ ] **Step 3: Launch the app for manual validation**

Run: `powershell -ExecutionPolicy Bypass -File scripts/run_app.ps1`
Expected:

- the skeleton panel shows the writing zone plus raw/stable pen-tip overlays
- slow block-letter writing produces fewer accidental stroke breaks
- pen-down starts cleanly after real motion instead of on the transition frame
- brief plausible tracking loss usually resumes the same stroke instead of splitting it
- canvas positioning feels more centered and controllable than the current build

## Self-Review

**Spec coverage**

- tracking-stage stabilization is covered by Task 1
- gesture intent and hysteresis are covered by Task 2
- continuity and dropout recovery are covered by Task 3
- writing-zone mapping and debug visibility are covered by Task 4
- configurable controls are covered by Task 5
- regression and manual feel validation are covered by Task 6

**Placeholder scan**

- no `TODO` or `TBD` placeholders remain
- each task includes exact file paths, test commands, and concrete code examples

**Type consistency**

- `PenPose`, `GestureClassifier`, `DeadzoneFilter`, `SessionController`, and writing-zone settings are named consistently across tasks
