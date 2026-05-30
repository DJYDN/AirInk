from airwrite.config.defaults import DEFAULT_SETTINGS_PAYLOAD
from airwrite.config.paths import AppPaths


def test_test_env_honors_explicit_directory_overrides(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))

    paths = AppPaths.from_env(project_root=tmp_path)

    assert paths.config_dir == tmp_path / "config"
    assert paths.data_dir == tmp_path / "data"
    assert paths.log_dir == tmp_path / "logs"


def test_test_env_uses_output_root_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.delenv("AIRWRITE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_DATA_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_LOG_DIR", raising=False)

    paths = AppPaths.from_env(project_root=tmp_path)

    assert paths.root_dir == tmp_path / "tests" / "output"
    assert paths.config_dir == paths.root_dir / "config"
    assert paths.data_dir == paths.root_dir / "data"
    assert paths.log_dir == paths.root_dir / "logs"


def test_dev_env_uses_data_dev_root_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("AIRWRITE_ENV", raising=False)
    monkeypatch.delenv("AIRWRITE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_DATA_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_LOG_DIR", raising=False)

    paths = AppPaths.from_env(project_root=tmp_path)

    assert paths.environment == "dev"
    assert paths.root_dir == tmp_path / "data" / "dev"
    assert paths.config_dir == paths.root_dir / "config"
    assert paths.data_dir == paths.root_dir / "data"
    assert paths.log_dir == paths.root_dir / "logs"


def test_named_non_test_env_uses_matching_data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRWRITE_ENV", "staging")
    monkeypatch.delenv("AIRWRITE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_DATA_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_LOG_DIR", raising=False)

    paths = AppPaths.from_env(project_root=tmp_path)

    assert paths.environment == "staging"
    assert paths.root_dir == tmp_path / "data" / "staging"
    assert paths.config_dir == paths.root_dir / "config"
    assert paths.data_dir == paths.root_dir / "data"
    assert paths.log_dir == paths.root_dir / "logs"


def test_default_settings_payload_matches_task_2_contract():
    assert DEFAULT_SETTINGS_PAYLOAD == {
        "camera": {
            "index": 0,
            "width": 1280,
            "height": 720,
            "fps": 30,
            "mirror": True,
        },
        "canvas": {
            "width": 1280,
            "height": 720,
            "background_color": "#FFFFFF",
        },
        "pen": {
            "color": "#000000",
            "width": 4,
            "opacity": 1.0,
        },
        "tracking": {
            "min_detection_confidence": 0.7,
            "min_tracking_confidence": 0.75,
            "landmark_smoothing": 0.55,
            "pinch_down_threshold": 0.28,
            "pinch_up_threshold": 0.34,
            "stable_frames": 3,
            "lost_frame_limit": 10,
            "gesture_stable_frames": 1,
            "fist_ratio_threshold": 0.65,
            "extended_ratio_threshold": 0.88,
            "session_idle_timeout_ms": 1500,
        },
        "filter": {
            "type": "one_euro",
            "strength": 0.5,
            "deadzone": 4.0,
            "start_threshold": 4.0,
            "max_jump_distance": 180.0,
        },
    }
