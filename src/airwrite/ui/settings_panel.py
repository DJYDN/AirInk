from PySide6.QtWidgets import QCheckBox, QFormLayout, QGroupBox, QVBoxLayout, QWidget


class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settings_panel")
        self.setMinimumWidth(220)

        layout = QVBoxLayout(self)
        group = QGroupBox("Settings")
        form = QFormLayout(group)
        self.mock_camera_checkbox = QCheckBox()
        self.mock_serial_checkbox = QCheckBox()
        form.addRow("Mock camera", self.mock_camera_checkbox)
        form.addRow("Mock serial", self.mock_serial_checkbox)
        layout.addWidget(group)
        layout.addStretch(1)
