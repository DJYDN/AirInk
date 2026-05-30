from PySide6.QtWidgets import QWidget

from airwrite.export.export_png import ensure_export_path, export_widget_to_png


def test_ensure_export_path_returns_path_with_filename(tmp_path):
    assert ensure_export_path(tmp_path, "snapshot.png") == tmp_path / "snapshot.png"


def test_export_widget_to_png_writes_png_file(qtbot, tmp_path):
    widget = QWidget()
    widget.resize(24, 24)

    qtbot.addWidget(widget)
    widget.show()

    export_path = export_widget_to_png(widget, tmp_path, "widget.png")

    assert export_path == tmp_path / "widget.png"
    assert export_path.exists()
    assert export_path.stat().st_size > 0
