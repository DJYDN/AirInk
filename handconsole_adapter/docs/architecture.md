# Architecture

## 1. Purpose

This adapter restructures AirInk as a HandConsole-style desktop application module while staying isolated from the existing AirInk implementation.

## 2. Target stack

```text
Frontend: React + TypeScript + Vite
State: Zustand
Routing: React Router
Visualization: Canvas / SVG / optional ECharts / optional Three.js
Desktop shell: Tauri 2
Backend: Rust
Communication: Tauri invoke commands + Tauri event streams
```

## 3. High-level data flow

```text
Camera / Mock / Playback source
        ↓
Tracking frame producer
        ↓
airink/tracking_frame event
        ↓
Zustand stores
        ↓
AirWriting canvas, debug panels, recognition UI
```

## 4. Backend module plan

```text
src-tauri/src/
├── lib.rs
├── camera.rs
├── tracking.rs
├── gesture.rs
├── stroke.rs
├── recognition.rs
├── session.rs
├── config.rs
└── logger.rs
```

### camera.rs

Responsibilities:

- Start and stop camera source
- Track camera status
- Emit camera status events
- Support mock camera mode

### tracking.rs

Responsibilities:

- Produce normalized tracking frames
- Bridge Python sidecar or mock data
- Emit `airink/tracking_frame`

### gesture.rs

Responsibilities:

- Compute pinch state
- Maintain pen state machine
- Debounce pen down/up
- Handle short hand-loss grace periods

### stroke.rs

Responsibilities:

- Map tracking coordinates to canvas coordinates
- Apply active region mapping
- Filter points
- Split and manage strokes

### recognition.rs

Responsibilities:

- Define recognition provider interface
- Provide placeholder recognition result
- Keep future OCR/LLM providers replaceable

### session.rs

Responsibilities:

- Record frames and strokes
- Save session metadata
- List sessions
- Playback frames and strokes

### config.rs

Responsibilities:

- Store AirInk-specific settings
- Store calibration profiles
- Save/load active profile

## 5. Frontend module plan

```text
src/
├── main.tsx
├── App.tsx
├── pages/
│   ├── AirInkDashboard.tsx
│   ├── AirWriting.tsx
│   ├── Calibration.tsx
│   ├── Recognition.tsx
│   ├── Playback.tsx
│   └── Settings.tsx
├── components/
│   ├── layout/
│   ├── camera/
│   ├── canvas/
│   ├── tracking/
│   ├── recognition/
│   └── calibration/
├── stores/
├── types/
└── utils/
```

## 6. Page responsibilities

### AirInkDashboard

- Show camera status
- Show tracking status
- Show FPS and latency
- Show current session summary

### AirWriting

- Main writing workspace
- Camera preview
- Skeleton overlay
- Writing canvas
- Gesture debug panel
- Recognition result panel

### Calibration

- Active writing region calibration
- Pinch threshold calibration
- Calibration profile save/load

### Recognition

- Candidate text display
- Candidate confirmation
- Recognition provider selection

### Playback

- Session list
- Session replay
- Delete session
- Export session

### Settings

- Camera settings
- Tracking settings
- Gesture thresholds
- Filter settings
- Canvas settings
- Recognition settings

## 7. Event naming convention

All adapter events use the `airink/` prefix:

```text
airink/camera_status
airink/tracking_frame
airink/gesture_state
airink/stroke_update
airink/session_status
airink/recognition_result
airink/playback_frame
```

## 8. Isolation rule

No existing file outside `handconsole_adapter/` should be changed during this refactor track.
