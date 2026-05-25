from airwrite.export.export_png import ensure_export_path


def test_ensure_export_path_returns_path_with_filename(tmp_path):
    assert ensure_export_path(tmp_path, "snapshot.png") == tmp_path / "snapshot.png"
