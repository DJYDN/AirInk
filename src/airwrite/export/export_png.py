from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWidget


def ensure_export_path(directory: str | Path, filename: str) -> Path:
    export_dir = Path(directory)
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir / filename


def export_widget_to_png(widget: QWidget, directory: str | Path, filename: str) -> Path:
    export_path = ensure_export_path(directory, filename)
    if not widget.grab().save(str(export_path), "PNG"):
        raise RuntimeError(f"Failed to export PNG to {export_path}")

    return export_path
