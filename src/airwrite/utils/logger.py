from __future__ import annotations

import logging
from pathlib import Path


def get_logger(name: str, log_dir: str | Path | None = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if log_dir is not None:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        target_file = log_path / f"{name.replace('.', '_')}.log"

        if not any(
            isinstance(handler, logging.FileHandler)
            and Path(handler.baseFilename) == target_file
            for handler in logger.handlers
        ):
            file_handler = logging.FileHandler(target_file, encoding="utf-8")
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            )
            logger.addHandler(file_handler)

    return logger
