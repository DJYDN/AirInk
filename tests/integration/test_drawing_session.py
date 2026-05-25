from airwrite.app import AirWriteApp


def test_test_app_session_can_add_mock_point_to_canvas(qtbot):
    app = AirWriteApp.for_test()
    window = app.window

    qtbot.addWidget(window)
    window.show()

    app.process_mock_point(12, 34)

    assert window.canvas.points == [(12, 34)]
