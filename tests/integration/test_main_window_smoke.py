from airwrite.ui.main_window import MainWindow


def test_main_window_can_be_created_and_shown(qtbot):
    window = MainWindow()

    qtbot.addWidget(window)
    window.show()

    assert window.isVisible()
    assert window.canvas is not None
    assert window.status_bar_widget is not None
