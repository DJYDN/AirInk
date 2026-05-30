# AirInk Python Sidecar Contract

## Purpose

The adapter can initially reuse the existing AirInk Python tracking pipeline as a sidecar process instead of rewriting camera capture and MediaPipe tracking in Rust.

The sidecar must output newline-delimited JSON records to stdout.

## Frame message

Each line should be a complete JSON object:

```json
{
  "timestamp_ms": 123456,
  "frame_id": 1,
  "hand_detected": true,
  "raw_tip": { "x": 0.52, "y": 0.31 },
  "stable_tip": { "x": 0.50, "y": 0.32 },
  "pinch_ratio": 0.27,
  "extension_ratio": 0.93,
  "confidence": 0.88
}
```

Coordinates should be normalized to `[0, 1]` in camera/image space.

## Process lifecycle

The future Rust bridge will own the sidecar lifecycle:

```text
Tauri command: airink_start_sidecar
        ↓
spawn python sidecar
        ↓
read stdout line by line
        ↓
parse SidecarTrackingFrame
        ↓
convert to AirInkFrame
        ↓
emit airink/tracking_frame
```

## Error handling

The sidecar should write structured errors to stderr or emit JSON messages with:

```json
{ "type": "error", "message": "camera open failed" }
```

## Compatibility rule

The sidecar contract should adapt to the current AirInk implementation. The existing AirInk runtime code should not be modified during the adapter stage unless explicitly requested.
