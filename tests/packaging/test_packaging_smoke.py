from pathlib import Path


def test_packaging_scripts_exist_and_reference_expected_entrypoints():
    project_root = Path(__file__).resolve().parents[2]
    run_script = project_root / "scripts" / "run_app.ps1"
    build_script = project_root / "scripts" / "build_exe.ps1"

    assert run_script.exists()
    assert build_script.exists()

    run_script_text = run_script.read_text(encoding="utf-8")
    build_script_text = build_script.read_text(encoding="utf-8")

    assert "python -m airwrite.main" in run_script_text
    assert "PyInstaller" in build_script_text
    assert "airwrite.main" in build_script_text
    assert "AirWrite.spec" in build_script_text


def test_runtime_data_and_build_artifacts_are_gitignored():
    project_root = Path(__file__).resolve().parents[2]
    gitignore_text = (project_root / ".gitignore").read_text(encoding="utf-8")

    assert "data/" in gitignore_text
    assert "dist/" in gitignore_text
    assert "build/" in gitignore_text
