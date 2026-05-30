# AirWrite Release Checklist

- Sync the branch and confirm the intended release commit is checked out.
- Run `./scripts/run_tests.ps1` and confirm the suite passes.
- Verify `scripts/run_app.ps1` launches the app from the local virtual environment.
- Run `./scripts/build_exe.ps1` to produce the Windows one-folder PyInstaller build.
- Smoke test the generated `dist/AirWrite` app: launch, draw a point, undo, clear, export PNG, and reopen to confirm settings persist.
- Confirm `tests/output` artifacts are not accidentally included in the packaged app.
- Record the tested Python, PySide6, and PyInstaller versions in release notes if they changed.
