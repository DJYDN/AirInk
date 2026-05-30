# Integration Contract

## 1. Purpose

This document defines the future contract between the AirInk adapter backend and frontend. It is designed to be compatible with a HandConsole-style Tauri event architecture.

## 2. Event stream overview

```text
Backend producer
  -> Tauri event
  -> frontend listener
  -> Zustand store
  -> page/component rendering
```

## 3. Events

### airink/camera_status

Payload:

```ts
export interface CameraStatusEvent {
  status: "idle" | "starting" | "running" | "error";
  camera_index: number;
  width: number;
  height: number;
  fps: number;
  error_message?: string;
}
```

### airink/tracking_frame

Payload:

```ts
export interface AirInkFrame {
  timestamp_ms: number;
  frame_id: number;
  source_type: "Camera" | "Mock" | "Playback";
  camera: {
    width: number;
    height: number;
    fps: number;
  };
  tracking: {
    hand_detected: boolean;
    confidence: number;
    landmarks: Point2D[];
    raw_tip: Point2D | null;
    stable_tip: Point2D | null;
    pinch_ratio: number | null;
    extension_ratio: number | null;
  };
  gesture: {
    state: "HOVER" | "ARMING_DOWN" | "INKING" | "ARMING_UP" | "HAND_LOST";
    drawing_active: boolean;
  };
  quality: {
    tracking_ok: boolean;
    jump_rejected: boolean;
    frame_dropped: boolean;
  };
}
```

### airink/stroke_update

Payload:

```ts
export interface StrokeUpdateEvent {
  session_id: string | null;
  active_stroke: Stroke | null;
  committed_strokes: Stroke[];
  stroke_count: number;
}
```

### airink/session_status

Payload:

```ts
export interface SessionStatusEvent {
  status: "idle" | "recording" | "pending_recognition" | "showing_candidates" | "playback";
  session_id: string | null;
  stroke_count: number;
}
```

### airink/recognition_result

Payload:

```ts
export interface RecognitionResultEvent {
  session_id: string | null;
  candidates: RecognitionCandidate[];
  provider: string;
  elapsed_ms: number;
}
```

### airink/playback_frame

Payload:

Same shape as `AirInkFrame`.

## 4. Commands

### Camera commands

```text
airink_start_camera(settings_json?: string)
airink_stop_camera()
airink_get_camera_status()
```

### Session commands

```text
airink_start_session(name?: string)
airink_stop_session()
airink_clear_session()
airink_undo_stroke()
airink_list_sessions()
airink_delete_session(session_id: string)
```

### Playback commands

```text
airink_start_playback(session_id: string, speed?: number)
airink_stop_playback()
```

### Recognition commands

```text
airink_recognize_current_session(provider?: string)
airink_confirm_candidate(candidate_id: string)
```

### Config commands

```text
airink_get_settings()
airink_set_settings(settings_json: string)
airink_get_calibration_profiles()
airink_save_calibration_profile(profile_json: string)
airink_set_active_calibration(profile_name: string)
airink_delete_calibration_profile(profile_name: string)
```

## 5. Shared primitive types

```ts
export interface Point2D {
  x: number;
  y: number;
}

export interface StrokePoint {
  x: number;
  y: number;
  t: number;
  confidence: number;
}

export interface Stroke {
  id: string;
  points: StrokePoint[];
}

export interface RecognitionCandidate {
  id: string;
  text: string;
  confidence: number | null;
}
```

## 6. Session storage contract

Recommended future session layout:

```text
sessions/
├── index.json
└── <session_id>/
    ├── metadata.json
    ├── frames.jsonl
    ├── strokes.json
    ├── recognition.json
    └── preview.png
```

## 7. Python sidecar contract

The adapter may reuse the current AirInk Python implementation through a sidecar process. The sidecar should output newline-delimited JSON frames.

Example:

```json
{"timestamp_ms":123456,"frame_id":1,"hand_detected":true,"raw_tip":{"x":0.5,"y":0.3},"stable_tip":{"x":0.49,"y":0.31},"pinch_ratio":0.27,"extension_ratio":0.93,"confidence":0.88}
```

The Rust bridge converts this into `airink/tracking_frame` events.

## 8. Compatibility notes

This contract is intentionally close to HandConsole's event-driven architecture, but uses its own `airink/` namespace so it can remain isolated until integration is explicitly requested.
