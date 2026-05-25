from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    project_root: Path
    environment: str
    root_dir: Path
    config_dir: Path
    data_dir: Path
    log_dir: Path

    @classmethod
    def from_env(cls, project_root: Path) -> "AppPaths":
        environment = os.getenv("AIRWRITE_ENV", "dev")
        default_root = (
            project_root / "tests" / "output"
            if environment == "test"
            else project_root / "data" / "dev"
        )

        return cls(
            project_root=project_root,
            environment=environment,
            root_dir=default_root,
            config_dir=Path(os.getenv("AIRWRITE_CONFIG_DIR", default_root / "config")),
            data_dir=Path(os.getenv("AIRWRITE_DATA_DIR", default_root / "data")),
            log_dir=Path(os.getenv("AIRWRITE_LOG_DIR", default_root / "logs")),
        )
