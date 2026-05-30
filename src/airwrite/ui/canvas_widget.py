from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from airwrite.trajectory.stroke import Stroke


class CanvasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("canvas_widget")
        self.setMinimumSize(640, 360)
        self.points: list[tuple[int, int]] = []
        self.strokes: list[Stroke] = []
        self.active_stroke: Stroke | None = None
        self._background_color = QColor("white")
        self._pen_color = QColor("black")
        self._pen_width = 4

    def add_point(self, x: int, y: int) -> tuple[int, int]:
        point = (int(x), int(y))
        self.points.append(point)
        self.update()
        return point

    def clear_points(self) -> None:
        self.points.clear()
        self.strokes = []
        self.active_stroke = None
        self.update()

    def undo_last_point(self) -> tuple[int, int] | None:
        if not self.points:
            return None

        point = self.points.pop()
        self.update()
        return point

    def set_pen_style(self, *, color: str, width: int) -> None:
        self._pen_color = QColor(color)
        self._pen_width = width
        self.update()

    def set_strokes(self, strokes: list[Stroke], active_stroke: Stroke | None = None) -> None:
        self.strokes = [Stroke(points=list(stroke.points)) for stroke in strokes]
        self.active_stroke = (
            Stroke(points=list(active_stroke.points)) if active_stroke is not None else None
        )
        flattened_points = [
            (int(point.x), int(point.y))
            for stroke in self.strokes
            for point in stroke.points
        ]
        if self.active_stroke is not None:
            flattened_points.extend(
                (int(point.x), int(point.y)) for point in self.active_stroke.points
            )
        self.points = flattened_points
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._background_color)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(
            QPen(
                self._pen_color,
                self._pen_width,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )

        if (not self.strokes and self.active_stroke is None) and len(self.points) == 1:
            x, y = self.points[0]
            painter.drawPoint(QPointF(x, y))
            return

        if not self.strokes and self.active_stroke is None:
            for start, end in zip(self.points, self.points[1:]):
                painter.drawLine(QPointF(*start), QPointF(*end))

        self._draw_strokes(painter, self.strokes)
        if self.active_stroke is not None:
            self._draw_strokes(painter, [self.active_stroke])

    def _draw_strokes(self, painter: QPainter, strokes: list[Stroke]) -> None:
        for stroke in strokes:
            if not stroke.points:
                continue

            if len(stroke.points) == 1:
                point = stroke.points[0]
                painter.drawPoint(QPointF(point.x, point.y))
                continue

            for start, end in zip(stroke.points, stroke.points[1:]):
                painter.drawLine(QPointF(start.x, start.y), QPointF(end.x, end.y))
