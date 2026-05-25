from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CanvasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("canvas_widget")
        self.setMinimumSize(640, 360)
        self.points: list[tuple[int, int]] = []

        layout = QVBoxLayout(self)
        label = QLabel("Canvas placeholder")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def add_point(self, x: int, y: int) -> tuple[int, int]:
        point = (int(x), int(y))
        self.points.append(point)
        self.update()
        return point

    def clear_points(self) -> None:
        self.points.clear()
        self.update()

    def undo_last_point(self) -> tuple[int, int] | None:
        if not self.points:
            return None

        point = self.points.pop()
        self.update()
        return point
