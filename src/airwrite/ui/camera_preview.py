from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CameraPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("camera_preview_widget")
        self.setMinimumHeight(180)

        layout = QVBoxLayout(self)
        label = QLabel("Camera preview placeholder")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
