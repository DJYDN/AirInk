from __future__ import annotations

import json

import pytest

from airwrite.config.defaults import default_settings_payload
from airwrite.config.paths import AppPaths
from airwrite.config.settings import AppSettings, SettingsManager


def test_default_settings_use_implemented_deadzone_filter() -> None:
    settings = AppSettings.defaults()

    assert settings.filter.type == "deadzone"


def test_default_settings_payload_returns_deep_copy() -> None:
    first = default_settings_payload()
    second = default_settings_payload()

    first["filter"]["type"] = "changed"

    assert second["filter"]["type"] == "deadzone"


def test_settings_manager_loads_defaults_when_config_is_missing(tmp_path) -> None:
    paths = _make_paths(tmp_path)
    manager = SettingsManager(paths)

    settings = manager.load()

    assert settings.camera.index == 0
    assert settings.filter.type == "deadzone"
    assert manager.config_path.exists()


def test_settings_manager_loads_defaults_when_config_is_invalid(tmp_path) -> None:
    paths = _make_paths(tmp_path)
    paths.config_dir.mkdir(parents=True)
    (paths.config_dir / "config.json").write_text("not-json", encoding="utf-8")
    manager = SettingsManager(paths)

    settings = manager.load()

    assert settings.filter.type == "deadzone"
    assert json.loads(manager.config_path.read_text(encoding="utf-8"))["filter"]["type"] == "deadzone"


def test_app_settings_rejects_unknown_missing_sections() -> None:
    payload = default_settings_payload()
    del payload["camera"]

    with pytest.raises(KeyError):
        AppSettings.from_dict(payload)


def _make_paths(tmp_path) -> AppPaths:
    return AppPaths(
        project_root=tmp_path,
        environment="test",
        root_dir=tmp_path,
        config_dir=tmp_path / "config",
        data_dir=tmp_path / "data",
        log_dir=tmp_path / "logs",
    )
