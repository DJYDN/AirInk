from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CanvasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("canvas_widget")
        self.setMinimumSize(640, 360)

        layout = QVBoxLayout(self)
        label = QLabel("Canvas placeholder")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
