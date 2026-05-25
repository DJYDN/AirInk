from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from airwrite.config.paths import AppPaths
from airwrite.config.settings import SettingsManager
from airwrite.export.export_png import export_widget_to_png
from airwrite.ui.main_window import MainWindow
from airwrite.utils.logger import get_logger


@dataclass
class AirWriteApp:
    qt_app: QApplication
    window: MainWindow
    paths: AppPaths
    settings_manager: SettingsManager
    owns_qt_app: bool

    def __post_init__(self) -> None:
        self.logger = get_logger("airwrite.app", self.paths.log_dir)
        self._loop_timer = QTimer(self.window)
        self._loop_timer.setInterval(16)
        self._loop_timer.timeout.connect(self._process_frame)

    @classmethod
    def create(cls) -> "AirWriteApp":
        return cls._build(test_mode=False)

    @classmethod
    def for_test(cls) -> "AirWriteApp":
        return cls._build(test_mode=True)

    @classmethod
    def _build(cls, *, test_mode: bool) -> "AirWriteApp":
        qt_app = QApplication.instance()
        owns_qt_app = qt_app is None
        if qt_app is None:
            qt_app = QApplication(sys.argv[:1])

        project_root = Path(__file__).resolve().parents[2]
        paths = AppPaths.from_env(project_root)
        settings_manager = SettingsManager(paths)
        settings_manager.load()
        window = MainWindow()

        app = cls(
            qt_app=qt_app,
            window=window,
            paths=paths,
            settings_manager=settings_manager,
            owns_qt_app=owns_qt_app,
        )
        app._wire_controls()
        if not test_mode:
            app.start_realtime_loop()
        return app

    def start_realtime_loop(self) -> None:
        if not self._loop_timer.isActive():
            self._loop_timer.start()

    def stop_realtime_loop(self) -> None:
        self._loop_timer.stop()

    def process_mock_point(self, x: int, y: int) -> tuple[int, int]:
        point = self.window.canvas.add_point(x, y)
        self.window.status_bar_widget.set_status(f"Drawing point at {point[0]}, {point[1]}")
        return point

    def clear_canvas(self) -> None:
        self.window.canvas.clear_points()
        self.window.status_bar_widget.set_status("Canvas cleared")

    def undo_last_stroke(self) -> tuple[int, int] | None:
        point = self.window.canvas.undo_last_point()
        if point is None:
            self.window.status_bar_widget.set_status("Nothing to undo")
        else:
            self.window.status_bar_widget.set_status("Undid last point")
        return point

    def export_png(self, filename: str | bool = "snapshot.png") -> Path:
        target_filename = filename if isinstance(filename, str) else "snapshot.png"
        export_path = export_widget_to_png(
            self.window.canvas,
            self.paths.data_dir,
            target_filename,
        )
        self.window.status_bar_widget.set_status(f"Exported PNG to {export_path.name}")
        return export_path

    def _wire_controls(self) -> None:
        self.window.undo_button.clicked.connect(self.undo_last_stroke)
        self.window.clear_button.clicked.connect(self.clear_canvas)
        self.window.export_button.clicked.connect(self.export_png)

    def run(self) -> int:
        self.window.show()
        self.start_realtime_loop()
        return self.qt_app.exec()

    def _process_frame(self) -> None:
        # Camera and hand-tracking work arrives in a later task.
        return None
