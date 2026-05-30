from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor

from airwrite.trajectory.stroke import Stroke, StrokePoint
from airwrite.ui.canvas_widget import CanvasWidget


def test_canvas_widget_renders_drawn_points(qtbot):
    widget = CanvasWidget()
    widget.resize(200, 120)
    qtbot.addWidget(widget)
    widget.show()
    qtbot.wait(10)

    before_image = widget.grab().toImage()
    before_color = before_image.pixelColor(QPoint(40, 50))

    widget.add_point(40, 50)
    widget.add_point(80, 70)
    qtbot.wait(10)

    image = widget.grab().toImage()
    sampled_colors = [image.pixelColor(QPoint(40, 50)), image.pixelColor(QPoint(80, 70))]

    assert image.pixelColor(QPoint(40, 50)) != before_color
    assert any(color != QColor("white") for color in sampled_colors)


def test_canvas_widget_renders_separate_strokes_without_cross_connection(qtbot):
    widget = CanvasWidget()
    widget.resize(200, 120)
    qtbot.addWidget(widget)
    widget.show()

    widget.set_strokes(
        [
            Stroke(
                points=[
                    StrokePoint(x=10.0, y=20.0, t=0.0, confidence=1.0),
                    StrokePoint(x=60.0, y=20.0, t=1.0, confidence=1.0),
                ]
            ),
            Stroke(
                points=[
                    StrokePoint(x=10.0, y=90.0, t=2.0, confidence=1.0),
                    StrokePoint(x=60.0, y=90.0, t=3.0, confidence=1.0),
                ]
            ),
        ]
    )
    qtbot.wait(10)

    image = widget.grab().toImage()

    assert image.pixelColor(QPoint(30, 20)) != QColor("white")
    assert image.pixelColor(QPoint(30, 90)) != QColor("white")
    assert image.pixelColor(QPoint(30, 55)) == QColor("white")
