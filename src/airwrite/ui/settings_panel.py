from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from airwrite.config.settings import AppSettings


class SettingsPanel(QWidget):
    settings_changed = Signal(object)
    _MAX_SPINBOX_VALUE = 2_147_483_647

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settings_panel")
        self.setMinimumWidth(220)
        self._is_loading = False
        self._base_settings = AppSettings.defaults()

        layout = QVBoxLayout(self)
        group = QGroupBox("Settings")
        form = QFormLayout(group)
        self.camera_index_spinbox = QSpinBox()
        self.camera_index_spinbox.setRange(0, self._MAX_SPINBOX_VALUE)
        self.pen_width_spinbox = QSpinBox()
        self.pen_width_spinbox.setRange(1, self._MAX_SPINBOX_VALUE)
        self.min_detection_confidence_spinbox = QDoubleSpinBox()
        self.min_detection_confidence_spinbox.setRange(0.0, 1.0)
        self.min_detection_confidence_spinbox.setSingleStep(0.05)
        self.min_detection_confidence_spinbox.setDecimals(2)
        self.min_tracking_confidence_spinbox = QDoubleSpinBox()
        self.min_tracking_confidence_spinbox.setRange(0.0, 1.0)
        self.min_tracking_confidence_spinbox.setSingleStep(0.05)
        self.min_tracking_confidence_spinbox.setDecimals(2)
        self.landmark_smoothing_spinbox = QDoubleSpinBox()
        self.landmark_smoothing_spinbox.setRange(0.0, 1.0)
        self.landmark_smoothing_spinbox.setSingleStep(0.05)
        self.landmark_smoothing_spinbox.setDecimals(2)
        self.gesture_stable_frames_spinbox = QSpinBox()
        self.gesture_stable_frames_spinbox.setRange(1, self._MAX_SPINBOX_VALUE)
        self.lost_frame_limit_spinbox = QSpinBox()
        self.lost_frame_limit_spinbox.setRange(1, self._MAX_SPINBOX_VALUE)
        self.deadzone_spinbox = QDoubleSpinBox()
        self.deadzone_spinbox.setRange(0.0, 1000.0)
        self.deadzone_spinbox.setSingleStep(0.5)
        self.deadzone_spinbox.setDecimals(1)
        self.start_threshold_spinbox = QDoubleSpinBox()
        self.start_threshold_spinbox.setRange(0.0, 1000.0)
        self.start_threshold_spinbox.setSingleStep(1.0)
        self.start_threshold_spinbox.setDecimals(1)
        self.max_jump_distance_spinbox = QDoubleSpinBox()
        self.max_jump_distance_spinbox.setRange(0.0, 5000.0)
        self.max_jump_distance_spinbox.setSingleStep(5.0)
        self.max_jump_distance_spinbox.setDecimals(1)
        self.mock_camera_checkbox = QCheckBox()
        self.mock_serial_checkbox = QCheckBox()
        self.camera_mirror_checkbox = QCheckBox()
        form.addRow("Camera index", self.camera_index_spinbox)
        form.addRow("Pen width", self.pen_width_spinbox)
        form.addRow("Detection confidence", self.min_detection_confidence_spinbox)
        form.addRow("Tracking confidence", self.min_tracking_confidence_spinbox)
        form.addRow("Landmark smoothing", self.landmark_smoothing_spinbox)
        form.addRow("Gesture stable frames", self.gesture_stable_frames_spinbox)
        form.addRow("Lost-frame grace", self.lost_frame_limit_spinbox)
        form.addRow("Deadzone", self.deadzone_spinbox)
        form.addRow("Start threshold", self.start_threshold_spinbox)
        form.addRow("Max jump", self.max_jump_distance_spinbox)
        form.addRow("Mirror camera", self.camera_mirror_checkbox)
        form.addRow("Mock camera", self.mock_camera_checkbox)
        form.addRow("Mock serial", self.mock_serial_checkbox)
        layout.addWidget(group)
        layout.addStretch(1)

        self.camera_index_spinbox.valueChanged.connect(self._emit_settings_changed)
        self.pen_width_spinbox.valueChanged.connect(self._emit_settings_changed)
        self.min_detection_confidence_spinbox.valueChanged.connect(self._emit_settings_changed)
        self.min_tracking_confidence_spinbox.valueChanged.connect(self._emit_settings_changed)
        self.landmark_smoothing_spinbox.valueChanged.connect(self._emit_settings_changed)
        self.gesture_stable_frames_spinbox.valueChanged.connect(self._emit_settings_changed)
        self.lost_frame_limit_spinbox.valueChanged.connect(self._emit_settings_changed)
        self.deadzone_spinbox.valueChanged.connect(self._emit_settings_changed)
        self.start_threshold_spinbox.valueChanged.connect(self._emit_settings_changed)
        self.max_jump_distance_spinbox.valueChanged.connect(self._emit_settings_changed)
        self.camera_mirror_checkbox.checkStateChanged.connect(self._emit_settings_changed)

    def load_settings(self, settings: AppSettings) -> None:
        self._base_settings = AppSettings.from_dict(settings.to_dict())
        self._is_loading = True
        try:
            self.camera_index_spinbox.setValue(settings.camera.index)
            self.pen_width_spinbox.setValue(settings.pen.width)
            self.min_detection_confidence_spinbox.setValue(settings.tracking.min_detection_confidence)
            self.min_tracking_confidence_spinbox.setValue(settings.tracking.min_tracking_confidence)
            self.landmark_smoothing_spinbox.setValue(settings.tracking.landmark_smoothing)
            self.gesture_stable_frames_spinbox.setValue(settings.tracking.gesture_stable_frames)
            self.lost_frame_limit_spinbox.setValue(settings.tracking.lost_frame_limit)
            self.deadzone_spinbox.setValue(settings.filter.deadzone)
            self.start_threshold_spinbox.setValue(settings.filter.start_threshold)
            self.max_jump_distance_spinbox.setValue(settings.filter.max_jump_distance)
            self.camera_mirror_checkbox.setChecked(settings.camera.mirror)
        finally:
            self._is_loading = False

    def current_settings(self) -> AppSettings:
        payload = self._base_settings.to_dict()
        payload["camera"]["index"] = self.camera_index_spinbox.value()
        payload["camera"]["mirror"] = self.camera_mirror_checkbox.isChecked()
        payload["pen"]["width"] = self.pen_width_spinbox.value()
        payload["tracking"]["min_detection_confidence"] = self.min_detection_confidence_spinbox.value()
        payload["tracking"]["min_tracking_confidence"] = self.min_tracking_confidence_spinbox.value()
        payload["tracking"]["landmark_smoothing"] = self.landmark_smoothing_spinbox.value()
        payload["tracking"]["gesture_stable_frames"] = self.gesture_stable_frames_spinbox.value()
        payload["tracking"]["lost_frame_limit"] = self.lost_frame_limit_spinbox.value()
        payload["filter"]["deadzone"] = self.deadzone_spinbox.value()
        payload["filter"]["start_threshold"] = self.start_threshold_spinbox.value()
        payload["filter"]["max_jump_distance"] = self.max_jump_distance_spinbox.value()
        return AppSettings.from_dict(payload)

    def _emit_settings_changed(self, *_args) -> None:
        if self._is_loading:
            return

        updated_settings = self.current_settings()
        self._base_settings = updated_settings
        self.settings_changed.emit(updated_settings)
