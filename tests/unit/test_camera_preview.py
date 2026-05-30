import numpy as np

from airwrite.ui.camera_preview import CameraPreviewWidget


def test_camera_preview_widget_renders_frame_into_label(qtbot):
    widget = CameraPreviewWidget()
    qtbot.addWidget(widget)
    frame = np.full((8, 12, 3), 128, dtype=np.uint8)

    widget.show_frame(frame)

    pixmap = widget.preview_label.pixmap()
    assert pixmap is not None
    assert not pixmap.isNull()
    assert widget.preview_label.text() == ""


def test_camera_preview_widget_scales_frame_to_fit_label(qtbot):
    widget = CameraPreviewWidget()
    widget.resize(120, 80)
    qtbot.addWidget(widget)
    widget.show()
    qtbot.wait(10)
    frame = np.full((240, 320, 3), 128, dtype=np.uint8)

    widget.show_frame(frame)

    pixmap = widget.preview_label.pixmap()
    assert pixmap is not None
    assert pixmap.width() <= widget.preview_label.width()
    assert pixmap.height() <= widget.preview_label.height()
