from pathlib import Path

from airwrite.app import AirWriteApp


def test_test_app_session_can_add_mock_point_to_canvas(qtbot):
    app = AirWriteApp.for_test()
    window = app.window

    qtbot.addWidget(window)
    window.show()

    app.process_mock_point(12, 34)

    assert window.canvas.points == [(12, 34)]


def test_control_surface_wires_undo_clear_and_export_actions(qtbot):
    app = AirWriteApp.for_test()
    window = app.window
    export_path = app.paths.data_dir / "snapshot.png"

    if export_path.exists():
        export_path.unlink()

    qtbot.addWidget(window)
    window.show()

    app.process_mock_point(12, 34)
    app.process_mock_point(56, 78)

    window.undo_requested.emit()
    assert window.canvas.points == [(12, 34)]

    window.clear_requested.emit()
    assert window.canvas.points == []

    window.export_requested.emit()
    assert export_path == Path(app.paths.data_dir) / "snapshot.png"
    assert export_path.exists()
