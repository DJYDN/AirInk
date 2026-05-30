# HandConsole Module Mapping

## 1. Purpose

This document maps HandConsole concepts to the AirInk adapter. The adapter is not integrated into HandConsole yet; this file describes the future module boundary.

## 2. Page mapping

| HandConsole page | AirInk adapter equivalent | Notes |
|---|---|---|
| Dashboard | AirInkDashboard | Overview of camera, tracking, gesture, session, recognition |
| Connection | CameraSource / TrackingSource | Camera, mock source, Python sidecar source |
| LiveData | TrackingDebug | Frame table, landmarks, pinch ratio, gesture state |
| Calibration | AirInkCalibration | Writing region and gesture threshold calibration |
| Playback | AirInkPlayback | Stroke/session replay |
| Logs | AirInkLogs | Future logs and diagnostics |
| Settings | AirInkSettings | Camera, tracking, gesture, filter, recognition settings |

## 3. Event mapping

| HandConsole event | AirInk adapter event |
|---|---|
| connection/status_changed | airink/camera_status |
| stream/frame | airink/tracking_frame |
| playback/frame | airink/playback_frame |
| stream/stats | airink/session_status or airink/stats |

## 4. Store mapping

| HandConsole store | AirInk adapter store |
|---|---|
| connectionStore | cameraStore / sourceStore |
| streamStore | airinkStore / strokeStore |
| layoutStore | layoutStore |
| settingsStore | settingsStore |
| liveDataViewStore | trackingViewStore |

## 5. Backend module mapping

| HandConsole Rust module | AirInk adapter Rust module |
|---|---|
| serial_manager.rs | camera.rs / sidecar.rs |
| ble_manager.rs | optional future sensor source |
| simulator.rs | mock_source.rs |
| frame.rs | frame.rs |
| frame_parser.rs | sidecar_parser.rs |
| session.rs | session.rs |
| config.rs | config.rs |
| log_reader.rs | logger.rs / diagnostics.rs |

## 6. Future integration checklist

When integration into HandConsole is explicitly requested, HandConsole would need changes similar to:

1. Add AirInk route in `App.tsx`.
2. Add AirInk item in `NavRail.tsx`.
3. Register AirInk backend modules in `src-tauri/src/lib.rs`.
4. Add AirInk stores under `src/stores/`.
5. Add AirInk pages and components under `src/pages/` and `src/components/`.
6. Add AirInk event listeners in the shared layout or an AirInk-specific layout.

This adapter stage does not perform those changes.
