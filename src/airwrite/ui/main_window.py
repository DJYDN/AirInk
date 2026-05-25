from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from airwrite.ui.camera_preview import CameraPreviewWidget
from airwrite.ui.canvas_widget import CanvasWidget
from airwrite.ui.settings_panel import SettingsPanel
from airwrite.ui.status_bar import StatusBarWidget


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("main_window")
        self.setWindowTitle("AirWrite")
        self.resize(1200, 720)

        self.canvas = CanvasWidget(self)
        self.camera_preview = CameraPreviewWidget(self)
        self.settings_panel = SettingsPanel(self)
        self.status_bar_widget = StatusBarWidget(self)

        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)

        content_layout = QVBoxLayout()
        content_layout.addWidget(self.camera_preview)
        content_layout.addWidget(self.canvas, 1)

        root_layout.addLayout(content_layout, 1)
        root_layout.addWidget(self.settings_panel)

        status_bar = self.statusBar()
        status_bar.addPermanentWidget(self.status_bar_widget, 1)
