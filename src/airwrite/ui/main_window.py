from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from airwrite.ui.camera_preview import CameraPreviewWidget
from airwrite.ui.canvas_widget import CanvasWidget
from airwrite.ui.settings_panel import SettingsPanel
from airwrite.ui.status_bar import StatusBarWidget


class MainWindow(QMainWindow):
    undo_requested = Signal()
    clear_requested = Signal()
    export_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("main_window")
        self.setWindowTitle("AirWrite")
        self.resize(1200, 720)

        self.canvas = CanvasWidget()
        self.camera_preview = CameraPreviewWidget()
        self.settings_panel = SettingsPanel()
        self.status_bar_widget = StatusBarWidget()
        self.undo_button = QPushButton("Undo")
        self.clear_button = QPushButton("Clear")
        self.export_button = QPushButton("Export PNG")
        self.undo_button.clicked.connect(self.undo_requested.emit)
        self.clear_button.clicked.connect(self.clear_requested.emit)
        self.export_button.clicked.connect(self.export_requested.emit)

        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)

        content_layout = QVBoxLayout()
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.undo_button)
        controls_layout.addWidget(self.clear_button)
        controls_layout.addWidget(self.export_button)
        controls_layout.addStretch(1)

        content_layout.addLayout(controls_layout)
        content_layout.addWidget(self.camera_preview)
        content_layout.addWidget(self.canvas, 1)

        root_layout.addLayout(content_layout, 1)
        root_layout.addWidget(self.settings_panel)

        status_bar = self.statusBar()
        status_bar.addPermanentWidget(self.status_bar_widget, 1)
