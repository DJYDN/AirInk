from airwrite.config.paths import AppPaths


def test_test_env_writes_stay_inside_project(tmp_path, monkeypatch):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))

    paths = AppPaths.from_env(project_root=tmp_path)

    assert paths.config_dir == tmp_path / "config"
    assert paths.data_dir == tmp_path / "data"
    assert paths.log_dir == tmp_path / "logs"
