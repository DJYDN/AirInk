# AirInk HandConsole Adapter Development Plan

## 1. Objective

Create a new isolated refactor track that adapts AirInk to the HandConsole application framework.

The adapter must stay inside `handconsole_adapter/` and must not modify existing AirInk or HandConsole files.

## 2. Architecture direction

The target architecture follows the HandConsole desktop model:

```text
Tauri 2 Rust backend
        ↓ commands / events
React + TypeScript frontend
        ↓ Zustand stores
Pages and reusable components
```

## 3. Phases

### Phase 0: Documentation and contract

Deliverables:

- `README.md`
- `docs/development_plan.md`
- `docs/architecture.md`
- `docs/integration_contract.md`
- `docs/migration_from_airwrite.md`
- `docs/handconsole_module_mapping.md`

Acceptance:

- Only files under `handconsole_adapter/` are added.
- The migration direction is clear.
- The adapter can be reviewed without touching existing runtime code.

### Phase 1: Desktop scaffold

Deliverables:

- Minimal React + TypeScript + Vite scaffold
- Minimal Tauri Rust scaffold
- Page shells matching AirInk functions
- Shared TypeScript data contracts

Pages:

- AirInkDashboard
- AirWriting
- Calibration
- Recognition
- Playback
- Settings

Acceptance:

- The folder structure matches a HandConsole-style desktop app.
- Frontend and backend module boundaries are explicit.

### Phase 2: Mock event pipeline

Deliverables:

- Mock tracking frame generator
- Zustand AirInk store
- Canvas mock stroke display
- Status display for hand detection, pinch ratio, gesture state, FPS

Events:

- `airink/camera_status`
- `airink/tracking_frame`
- `airink/stroke_update`
- `airink/session_status`
- `airink/recognition_result`

Acceptance:

- Mock data can drive the frontend without a real camera.

### Phase 3: Python sidecar bridge

Deliverables:

- Sidecar contract for current AirInk Python tracking pipeline
- JSON line or local WebSocket event bridge
- Rust command wrappers to start and stop the sidecar

Acceptance:

- Existing AirInk logic can be reused without modifying current files.

### Phase 4: AirWriting MVP

Deliverables:

- Camera preview panel
- Skeleton overlay
- Writing canvas
- Pinch state debug panel
- Recognition panel
- Undo / Clear / Export controls

Acceptance:

- Real or mock tracking data produces strokes on canvas.

### Phase 5: Calibration

Deliverables:

- Active-region calibration wizard
- Pinch down/up threshold sampling
- Calibration profile save/load contract

Acceptance:

- Users can calibrate writing region and gesture thresholds without editing config files.

### Phase 6: Session recording and playback

Deliverables:

- Session metadata
- Frame JSONL recording
- Stroke JSON recording
- Playback event stream

Acceptance:

- Users can record, list, replay, and delete AirInk writing sessions.

### Phase 7: Recognition provider system

Deliverables:

- Placeholder recognizer
- Local recognizer interface
- Cloud recognizer interface
- Candidate confirmation workflow

Acceptance:

- The recognition workflow is provider-based and replaceable.

### Phase 8: HandConsole integration preparation

Deliverables:

- `docs/handconsole_integration_steps.md`
- Clear list of future HandConsole changes required

Acceptance:

- The adapter can be reviewed as a module candidate for HandConsole.

## 4. Immediate task list

| ID | Task | Priority |
|---|---|---|
| T001 | Add adapter README | P0 |
| T002 | Add development plan | P0 |
| T003 | Add architecture document | P0 |
| T004 | Add integration contract | P0 |
| T005 | Add desktop scaffold files | P0 |
| T006 | Add shared TypeScript contracts | P0 |
| T007 | Add Rust Tauri scaffold | P0 |
| T008 | Add mock event design | P1 |
| T009 | Add AirWriting page scaffold | P1 |
| T010 | Add calibration wizard design | P1 |

## 5. Commit rule

Every commit in this refactor track should only touch:

```text
handconsole_adapter/**
```
