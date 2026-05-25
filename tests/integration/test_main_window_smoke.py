from pytestqt.qtbot import QtBot

from airwrite.ui.main_window import MainWindow


def test_main_window_can_be_created_and_shown(qtbot):
    window = MainWindow()

    qtbot.addWidget(window)
    window.show()

    assert window.isVisible()
    assert window.canvas is not None
    assert window.camera_preview is not None
    assert window.settings_panel is not None
    assert window.status_bar_widget is not None
    assert window.settings_panel.mock_camera_checkbox is not None
    assert window.settings_panel.mock_serial_checkbox is not None
    assert window.undo_button is not None
    assert window.clear_button is not None
    assert window.export_button is not None
    assert window.statusBar().findChild(
        type(window.status_bar_widget),
        window.status_bar_widget.objectName(),
    ) is window.status_bar_widget


def test_main_window_buttons_emit_semantic_intent_signals(qtbot: QtBot):
    window = MainWindow()

    qtbot.addWidget(window)
    window.show()

    with qtbot.waitSignal(window.undo_requested, timeout=1000):
        window.undo_button.click()

    with qtbot.waitSignal(window.clear_requested, timeout=1000):
        window.clear_button.click()

    with qtbot.waitSignal(window.export_requested, timeout=1000):
        window.export_button.click()
