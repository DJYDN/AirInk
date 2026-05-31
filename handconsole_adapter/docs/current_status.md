# Current Status

## Isolation guarantee

All adapter work is currently isolated under:

```text
handconsole_adapter/
```

No existing AirInk runtime files and no HandConsole files are modified by this adapter track.

## Implemented adapter areas

### Documentation

- Development plan
- Architecture design
- Integration contract
- Migration plan from current AirInk/AirWrite
- HandConsole module mapping
- Future HandConsole integration steps
- Python sidecar contract

### Frontend scaffold

- React + TypeScript + Vite scaffold
- React Router pages
- Zustand store
- Dashboard page
- AirWriting page
- Calibration page
- Playback page
- Recognition page
- Settings page
- Skeleton overlay
- SVG writing canvas
- Mock stream controls
- Sidecar controls and sidecar error display

### Tauri/Rust scaffold

- Tauri config
- Cargo manifest
- build.rs
- binary entrypoint
- Rust frame types
- mock frame stream
- in-memory session registry
- calibration profile registry
- Python JSONL sidecar bridge

## Working data paths

### Mock stream path

```text
airink_start_mock_stream
  -> Rust mock frame generator
  -> airink/camera_status
  -> airink/session_status
  -> airink/tracking_frame
  -> React listener
  -> Zustand store
  -> Dashboard / AirWriting / SkeletonOverlay / WritingCanvas
```

### Playback path

```text
airink_list_sessions
  -> Playback UI
  -> airink_start_playback
  -> airink/playback_frame
  -> airink/tracking_frame
  -> existing frame display path
```

### Calibration path

```text
airink_get_calibration_profiles
  -> Calibration UI
  -> save / activate / delete profile commands
```

### Sidecar path

```text
airink_start_sidecar
  -> spawn Python process
  -> read stdout JSON Lines
  -> parse SidecarTrackingFrame
  -> convert to AirInkFrame
  -> emit airink/tracking_frame
```

Sidecar stderr and parse errors emit:

```text
airink/sidecar_error
```

## Known limitations

1. Session storage is currently in-memory only.
2. Calibration profiles are currently in-memory only.
3. The mock sidecar path is a relative argument and may need adjustment depending on the runtime working directory.
4. The sidecar bridge expects one valid JSON object per stdout line.
5. Recognition is still only a UI scaffold.
6. The adapter has not yet been compiled in CI.
7. The current adapter does not yet call the existing AirInk Python modules directly; it uses a contract-compatible mock sidecar.

## Recommended next steps

1. Run `handconsole_adapter/scripts/check.ps1` locally and fix compile errors.
2. Replace in-memory session registry with file-backed session storage.
3. Replace in-memory calibration registry with file-backed profile storage.
4. Add Recognition provider interface and placeholder backend command.
5. Add a sidecar path selector using a file dialog.
6. Add an explicit `airink_start_mock_sidecar` command that resolves the bundled mock sidecar path safely.
7. After validation, plan a controlled migration into HandConsole if still desired.
