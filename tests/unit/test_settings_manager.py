import json

from airwrite.config.defaults import DEFAULT_SETTINGS_PAYLOAD
from airwrite.config.paths import AppPaths
from airwrite.config.settings import SettingsManager


def test_load_missing_config_returns_defaults_and_writes_file(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.delenv("AIRWRITE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_DATA_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_LOG_DIR", raising=False)

    paths = AppPaths.from_env(project_root=tmp_path)
    manager = SettingsManager(paths)

    settings = manager.load()

    assert settings.to_dict() == DEFAULT_SETTINGS_PAYLOAD
    assert manager.config_path.exists()
    assert json.loads(manager.config_path.read_text(encoding="utf-8")) == DEFAULT_SETTINGS_PAYLOAD


def test_load_invalid_config_restores_defaults_and_leaves_config_present(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.delenv("AIRWRITE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_DATA_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_LOG_DIR", raising=False)

    paths = AppPaths.from_env(project_root=tmp_path)
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    config_path = paths.config_dir / "config.json"
    config_path.write_text("{not valid json", encoding="utf-8")

    manager = SettingsManager(paths)

    settings = manager.load()

    assert settings.to_dict() == DEFAULT_SETTINGS_PAYLOAD
    assert manager.config_path.exists()
    assert json.loads(manager.config_path.read_text(encoding="utf-8")) == DEFAULT_SETTINGS_PAYLOAD


def test_load_semantically_invalid_config_restores_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.delenv("AIRWRITE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_DATA_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_LOG_DIR", raising=False)

    paths = AppPaths.from_env(project_root=tmp_path)
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    config_path = paths.config_dir / "config.json"
    invalid_payload = {
        **DEFAULT_SETTINGS_PAYLOAD,
        "camera": {
            **DEFAULT_SETTINGS_PAYLOAD["camera"],
            "fps": "30",
        },
        "tracking": {
            **DEFAULT_SETTINGS_PAYLOAD["tracking"],
            "stable_frames": 0,
        },
    }
    config_path.write_text(json.dumps(invalid_payload, indent=2), encoding="utf-8")

    manager = SettingsManager(paths)

    settings = manager.load()

    assert settings.to_dict() == DEFAULT_SETTINGS_PAYLOAD
    assert manager.config_path.exists()
    assert json.loads(manager.config_path.read_text(encoding="utf-8")) == DEFAULT_SETTINGS_PAYLOAD


def test_save_persists_typed_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.delenv("AIRWRITE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_DATA_DIR", raising=False)
    monkeypatch.delenv("AIRWRITE_LOG_DIR", raising=False)

    paths = AppPaths.from_env(project_root=tmp_path)
    manager = SettingsManager(paths)
    settings = manager.load()
    settings.pen.color = "#336699"
    settings.tracking.stable_frames = 5

    manager.save(settings)

    reloaded = json.loads(manager.config_path.read_text(encoding="utf-8"))
    assert reloaded["pen"]["color"] == "#336699"
    assert reloaded["tracking"]["stable_frames"] == 5
