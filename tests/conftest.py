from pathlib import Path
import os


def pytest_sessionstart(session):
    output_root = Path("tests/output")
    (output_root / "config").mkdir(parents=True, exist_ok=True)
    (output_root / "data").mkdir(parents=True, exist_ok=True)
    (output_root / "logs").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("AIRWRITE_ENV", "test")
    os.environ.setdefault("AIRWRITE_CONFIG_DIR", str(output_root / "config"))
    os.environ.setdefault("AIRWRITE_DATA_DIR", str(output_root / "data"))
    os.environ.setdefault("AIRWRITE_LOG_DIR", str(output_root / "logs"))
