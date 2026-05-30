import json

from airwrite.app import AirWriteApp
from airwrite.config.defaults import DEFAULT_SETTINGS_PAYLOAD
from airwrite.ui.status_bar import StatusBarWidget


def test_app_loads_persisted_settings_into_settings_panel(tmp_path, monkeypatch, qtbot):
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    log_dir = tmp_path / "logs"
    config_dir.mkdir(parents=True, exist_ok=True)
    persisted_payload = {
        **DEFAULT_SETTINGS_PAYLOAD,
        "camera": {
            **DEFAULT_SETTINGS_PAYLOAD["camera"],
            "index": 2,
        },
        "pen": {
            **DEFAULT_SETTINGS_PAYLOAD["pen"],
            "width": 9,
        },
    }
    (config_dir / "config.json").write_text(json.dumps(persisted_payload), encoding="utf-8")
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(data_dir))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(log_dir))

    app = AirWriteApp.for_test()
    qtbot.addWidget(app.window)

    assert app.window.settings_panel.camera_index_spinbox.value() == 2
    assert app.window.settings_panel.pen_width_spinbox.value() == 9


def test_app_saves_settings_when_settings_panel_changes(tmp_path, monkeypatch, qtbot):
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(data_dir))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(log_dir))

    app = AirWriteApp.for_test()
    qtbot.addWidget(app.window)

    app.window.settings_panel.camera_index_spinbox.setValue(3)
    app.window.settings_panel.pen_width_spinbox.setValue(7)

    saved_payload = json.loads((config_dir / "config.json").read_text(encoding="utf-8"))
    assert saved_payload["camera"]["index"] == 3
    assert saved_payload["pen"]["width"] == 7


def test_out_of_range_but_valid_persisted_values_are_preserved_when_other_field_changes(
    tmp_path, monkeypatch, qtbot
):
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    log_dir = tmp_path / "logs"
    config_dir.mkdir(parents=True, exist_ok=True)
    persisted_payload = {
        **DEFAULT_SETTINGS_PAYLOAD,
        "camera": {
            **DEFAULT_SETTINGS_PAYLOAD["camera"],
            "index": 42,
            "mirror": True,
        },
        "pen": {
            **DEFAULT_SETTINGS_PAYLOAD["pen"],
            "width": 96,
        },
    }
    (config_dir / "config.json").write_text(json.dumps(persisted_payload), encoding="utf-8")
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(data_dir))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(log_dir))

    app = AirWriteApp.for_test()
    qtbot.addWidget(app.window)

    assert app.window.settings_panel.camera_index_spinbox.value() == 42
    assert app.window.settings_panel.pen_width_spinbox.value() == 96

    app.window.settings_panel.camera_mirror_checkbox.setChecked(False)

    saved_payload = json.loads((config_dir / "config.json").read_text(encoding="utf-8"))
    assert saved_payload["camera"]["index"] == 42
    assert saved_payload["pen"]["width"] == 96
    assert saved_payload["camera"]["mirror"] is False


def test_camera_mirror_setting_persists_when_toggled(tmp_path, monkeypatch, qtbot):
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(data_dir))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(log_dir))

    app = AirWriteApp.for_test()
    qtbot.addWidget(app.window)

    app.window.settings_panel.camera_mirror_checkbox.setChecked(False)

    saved_payload = json.loads((config_dir / "config.json").read_text(encoding="utf-8"))
    assert saved_payload["camera"]["mirror"] is False


def test_status_bar_metrics_preserve_existing_telemetry_on_drawing_only_updates(qtbot):
    widget = StatusBarWidget()
    qtbot.addWidget(widget)

    widget.set_metrics(drawing_active=False, fps=24.5, latency_ms=18.2, confidence=0.93)
    widget.set_metrics(drawing_active=True)

    assert widget._metrics_label.text() == (
        "Drawing: active | FPS: 24.5 | Latency: 18.2 ms | Confidence: 0.93"
    )


def test_interaction_tuning_controls_persist_when_changed(tmp_path, monkeypatch, qtbot):
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(data_dir))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(log_dir))

    app = AirWriteApp.for_test()
    qtbot.addWidget(app.window)

    app.window.settings_panel.min_detection_confidence_spinbox.setValue(0.8)
    app.window.settings_panel.min_tracking_confidence_spinbox.setValue(0.75)
    app.window.settings_panel.landmark_smoothing_spinbox.setValue(0.65)
    app.window.settings_panel.gesture_stable_frames_spinbox.setValue(3)
    app.window.settings_panel.lost_frame_limit_spinbox.setValue(10)
    app.window.settings_panel.deadzone_spinbox.setValue(5.5)
    app.window.settings_panel.start_threshold_spinbox.setValue(20.0)
    app.window.settings_panel.max_jump_distance_spinbox.setValue(220.0)

    saved_payload = json.loads((config_dir / "config.json").read_text(encoding="utf-8"))
    assert saved_payload["tracking"]["min_detection_confidence"] == 0.8
    assert saved_payload["tracking"]["min_tracking_confidence"] == 0.75
    assert saved_payload["tracking"]["landmark_smoothing"] == 0.65
    assert saved_payload["tracking"]["gesture_stable_frames"] == 3
    assert saved_payload["tracking"]["lost_frame_limit"] == 10
    assert saved_payload["filter"]["deadzone"] == 5.5
    assert saved_payload["filter"]["start_threshold"] == 20.0
    assert saved_payload["filter"]["max_jump_distance"] == 220.0
