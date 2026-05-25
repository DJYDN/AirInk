from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget


class StatusBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("status_bar_widget")
        layout = QHBoxLayout(self)
        self._label = QLabel("Ready")
        layout.addWidget(self._label)

    def set_status(self, message: str) -> None:
        self._label.setText(message)
