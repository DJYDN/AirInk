# AirWrite Testing Strategy

AirWrite uses a small test pyramid tuned for a desktop MVP.

- `tests/unit` covers pure logic, settings validation, and UI state wiring that can be exercised without full app flows.
- `tests/integration` covers app-level Qt behavior such as window creation, semantic button signals, and drawing/export flows.
- `tests/packaging` covers release scaffolding like launcher and build scripts without triggering a real executable build in CI.

All test runs should use sandbox-safe output paths under `tests/output` by setting `AIRWRITE_ENV=test` plus explicit config, data, and log directories.

Recommended commands:

```powershell
./scripts/run_tests.ps1
```

```powershell
.\.venv\Scripts\python -m pytest tests/unit/test_settings_persistence_ui.py tests/packaging/test_packaging_smoke.py
```
