# Future HandConsole Integration Steps

## 1. Current status

The AirInk adapter currently lives fully inside the AirInk repository under:

```text
handconsole_adapter/
```

It is not integrated into HandConsole yet. This keeps both existing projects safe while the adapter architecture is validated.

## 2. Future integration target

Future integration would add AirInk as a HandConsole module with pages such as:

```text
/airink
/airink/writing
/airink/calibration
/airink/playback
/airink/settings
```

## 3. Required HandConsole frontend changes

When integration is explicitly requested, HandConsole would need:

1. Add AirInk routes in `apps/desktop/src/App.tsx`.
2. Add navigation item in `apps/desktop/src/components/layout/NavRail.tsx`.
3. Add AirInk pages under `apps/desktop/src/pages/` or `apps/desktop/src/pages/airink/`.
4. Add AirInk components under `apps/desktop/src/components/airink/`.
5. Add AirInk store under `apps/desktop/src/stores/airinkStore.ts`.
6. Add AirInk types under `apps/desktop/src/types/airink.ts` or a dedicated folder.
7. Add event listeners for:

```text
airink/camera_status
airink/tracking_frame
airink/stroke_update
airink/session_status
airink/recognition_result
airink/playback_frame
airink/sidecar_error
```

## 4. Required HandConsole backend changes

HandConsole `src-tauri/src/lib.rs` would need to register AirInk modules and commands:

```text
airink_get_camera_status
airink_start_mock_stream
airink_stop_mock_stream
airink_start_sidecar
airink_stop_sidecar
airink_list_sessions
airink_start_playback
airink_stop_playback
airink_get_calibration_profiles
airink_save_calibration_profile
airink_set_active_calibration
airink_delete_calibration_profile
```

Recommended backend module layout:

```text
src-tauri/src/airink/
├── mod.rs
├── frame.rs
├── camera.rs
├── sidecar.rs
├── gesture.rs
├── stroke.rs
├── session.rs
├── config.rs
└── recognition.rs
```

## 5. Integration order

Recommended order:

1. Copy shared types and event contract.
2. Add page shells and navigation.
3. Add mock stream backend commands.
4. Validate mock stream in HandConsole UI.
5. Add sidecar bridge.
6. Add persistent session storage.
7. Add calibration profile persistence.
8. Add recognition provider system.

## 6. Compatibility rule

Do not directly copy the entire adapter into HandConsole at once. Migrate one module at a time, starting from mock stream and UI shell.

## 7. Open decisions

- Whether AirInk should be a first-class HandConsole page group or an optional plugin-like module.
- Whether sidecar Python should be packaged with HandConsole or configured externally.
- Whether AirInk session storage should share HandConsole session infrastructure or use a separate namespace.
- Whether camera source should be managed by Rust, Python sidecar, or a dedicated native plugin.
