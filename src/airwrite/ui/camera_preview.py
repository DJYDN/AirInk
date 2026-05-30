from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from airwrite.tracking.landmarks import Point2D


@dataclass(frozen=True)
class PreviewOverlay:
    gesture: str | None = None
    active_region: tuple[float, float, float, float] | None = None
    raw_tip: Point2D | None = None
    stable_tip: Point2D | None = None


class CameraPreviewWidget(QWidget):
    def __init__(self, title: str = "Camera", parent=None):
        super().__init__(parent)
        self.setObjectName("camera_preview_widget")
        self.setMinimumHeight(180)
        self._source_pixmap: QPixmap | None = None
        self._overlay: PreviewOverlay | None = None

        layout = QVBoxLayout(self)
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label = QLabel("Camera preview placeholder")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(180)
        layout.addWidget(self.title_label)
        layout.addWidget(self.preview_label)

    def show_placeholder(self, message: str = "Camera preview placeholder") -> None:
        self._source_pixmap = None
        self._overlay = None
        self.preview_label.clear()
        self.preview_label.setText(message)

    def show_frame(self, frame: np.ndarray) -> None:
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError("camera preview expects an HxWx3 frame")

        contiguous_frame = np.ascontiguousarray(frame)
        height, width, _channels = contiguous_frame.shape
        bytes_per_line = contiguous_frame.strides[0]
        image = QImage(
            contiguous_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_BGR888,
        ).copy()
        self._source_pixmap = QPixmap.fromImage(image)
        self._update_scaled_pixmap()
        self.preview_label.setText("")

    def set_overlay(self, overlay: PreviewOverlay | None) -> None:
        self._overlay = overlay

    def current_overlay(self) -> PreviewOverlay | None:
        return self._overlay

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self) -> None:
        if self._source_pixmap is None or self._source_pixmap.isNull():
            return

        scaled_pixmap = self._source_pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled_pixmap)
