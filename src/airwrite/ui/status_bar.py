from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class StatusBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("status_bar_widget")
        self._drawing_active = False
        self._fps: float | None = None
        self._latency_ms: float | None = None
        self._confidence: float | None = None
        layout = QHBoxLayout(self)
        self._status_label = QLabel("Ready")
        self._metrics_label = QLabel("Drawing: idle | FPS: -- | Latency: -- ms | Confidence: --")
        layout.addWidget(self._status_label, 1)
        layout.addWidget(self._metrics_label)

    def set_status(self, message: str) -> None:
        self._status_label.setText(message)

    def set_metrics(
        self,
        *,
        drawing_active: bool,
        fps: float | None = None,
        latency_ms: float | None = None,
        confidence: float | None = None,
    ) -> None:
        self._drawing_active = drawing_active
        if fps is not None:
            self._fps = fps
        if latency_ms is not None:
            self._latency_ms = latency_ms
        if confidence is not None:
            self._confidence = confidence

        drawing_state = "active" if self._drawing_active else "idle"
        fps_text = "--" if self._fps is None else f"{self._fps:.1f}"
        latency_text = "--" if self._latency_ms is None else f"{self._latency_ms:.1f}"
        confidence_text = "--" if self._confidence is None else f"{self._confidence:.2f}"
        self._metrics_label.setText(
            f"Drawing: {drawing_state} | FPS: {fps_text} | Latency: {latency_text} ms | Confidence: {confidence_text}"
        )
