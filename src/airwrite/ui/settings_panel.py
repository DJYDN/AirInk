from PySide6.QtWidgets import QCheckBox, QFormLayout, QGroupBox, QVBoxLayout, QWidget


class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settings_panel")
        self.setMinimumWidth(220)

        layout = QVBoxLayout(self)
        group = QGroupBox("Settings")
        form = QFormLayout(group)
        form.addRow("Mock camera", QCheckBox())
        form.addRow("Mock serial", QCheckBox())
        layout.addWidget(group)
        layout.addStretch(1)
