# Migration From Current AirInk / AirWrite

## 1. Current position

The existing AirInk implementation is a Python desktop MVP using a PySide6 UI, OpenCV camera access, MediaPipe hand tracking, gesture classification, stroke filtering, and a placeholder OCR provider.

This adapter does not replace that implementation. It creates a new architecture track that can eventually host the same capabilities in a HandConsole-style desktop framework.

## 2. Migration principle

Do not rewrite everything at once.

Recommended order:

```text
1. Define shared data contracts
2. Build mock tracking stream
3. Build React canvas and debug UI
4. Bridge existing Python tracking as a sidecar
5. Move pure algorithms into portable modules
6. Replace sidecar with native or optimized backend only if needed
```

## 3. Feature mapping

| Current AirInk area | Adapter target |
|---|---|
| PySide6 main window | React pages and layout components |
| Camera preview widget | CameraPreview component |
| Skeleton preview | SkeletonOverlay component |
| Canvas widget | WritingCanvas component |
| GestureClassifier | Rust or TypeScript gesture state module |
| PenPose and pinch ratio | Tracking frame model |
| DeadzoneFilter | Stroke pipeline filter module |
| SessionController | Session store + backend session module |
| Placeholder OCR | Recognition provider contract |
| SettingsManager | Tauri config module + Zustand settings store |

## 4. Sidecar-first strategy

The current Python tracking code should initially remain unchanged.

A small adapter process can import or call the existing AirInk tracking pipeline and emit JSON lines. The Tauri backend can spawn this sidecar, parse JSON, and emit `airink/tracking_frame` events.

Benefits:

- Low risk
- No immediate Rust MediaPipe rewrite
- Existing camera/tracking behavior can be compared against the new UI
- Faster path to a working HandConsole-style prototype

## 5. Algorithms that can be migrated later

Good candidates for future migration:

- Pinch ratio calculation
- Gesture debounce state machine
- Active region mapping
- Stroke filtering
- Session stroke model

Less urgent candidates:

- MediaPipe hand tracking backend
- OCR provider
- Camera device management

## 6. Compatibility and rollback

Because all adapter files live under `handconsole_adapter/`, rollback is simple:

```text
remove handconsole_adapter/
```

No existing AirInk runtime behavior should change during this refactor track.
