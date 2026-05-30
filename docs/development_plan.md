# AirInk Development Plan

## Goal

Build a Windows-first desktop MVP for camera-based air writing. The application should track hand motion from a regular camera, map the writing gesture to a canvas, export strokes, and later connect to real handwriting recognition.

## Current baseline

The current code already includes:

- PySide6 desktop UI.
- OpenCV camera source.
- MediaPipe hand landmark provider.
- Index-finger pen-pose estimation.
- Gesture state machine based on finger extension ratio.
- Stroke collection and canvas rendering.
- Deadzone-style trajectory filtering.
- PNG export.
- Placeholder OCR candidate flow.

## Phase 0: Engineering cleanup

Priority: P0

Tasks:

1. Remove machine-specific paths from dependency lock files.
2. Keep default settings aligned with implemented behavior.
3. Add basic unit tests for pure logic modules.
4. Improve project documentation.
5. Keep test output isolated from normal application data.

Acceptance criteria:

- A new developer can set up the project without editing local paths.
- Default config values describe real implemented code paths.
- Core logic can be tested without a camera.

## Phase 1: Drawing stability

Priority: P0 to P1

Tasks:

1. Improve pen-down and pen-up behavior.
2. Add a pinch-based gesture mode.
3. Add active writing-region calibration.
4. Improve gap handling when tracking is briefly lost.
5. Add a real low-latency smoothing filter such as One Euro Filter.

Acceptance criteria:

- The user can draw continuous strokes with low jitter.
- Short hand-tracking gaps do not destroy the session.
- Large jumps are split or rejected predictably.

## Phase 2: Recognition

Priority: P1 to P2

Tasks:

1. Move the OCR provider interface into a dedicated recognition package.
2. Render strokes to normalized recognition images.
3. Add at least one real recognition backend.
4. Keep placeholder recognition available for tests.
5. Support candidate confirmation and later text accumulation.

Acceptance criteria:

- Recognition code is replaceable without changing the UI flow.
- A session can produce real text candidates.

## Phase 3: Product usability

Priority: P2

Tasks:

1. Add better startup and camera-status messages.
2. Add a compact debug panel.
3. Add keyboard shortcuts.
4. Add fullscreen writing mode.
5. Add SVG or JSON stroke export.

Acceptance criteria:

- A non-developer can understand the current camera and tracking state.
- Common actions are accessible from buttons and shortcuts.

## Phase 4: Windows packaging

Priority: P2

Tasks:

1. Add a PyInstaller build script.
2. Bundle or validate the hand-landmarker model.
3. Document first-run behavior.
4. Add a smoke test for the packaged entry point.

Acceptance criteria:

- A Windows user can run the app from a packaged folder without setting up a Python environment manually.

## Immediate task list

| ID | Task | Priority |
| --- | --- | --- |
| T001 | Remove local editable path from requirements.lock.txt | P0 |
| T002 | Change default filter type to deadzone | P0 |
| T003 | Add tests for coordinate mapping | P0 |
| T004 | Add tests for trajectory filters | P0 |
| T005 | Add tests for gesture state transitions | P0 |
| T006 | Add tests for session controller | P1 |
| T007 | Document calibration design | P1 |
| T008 | Design recognition provider package | P1 |
