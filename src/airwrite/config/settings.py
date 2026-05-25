from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from json import JSONDecodeError
from pathlib import Path

from airwrite.config.defaults import default_settings_payload
from airwrite.config.paths import AppPaths


@dataclass
class CameraSettings:
    index: int
    width: int
    height: int
    fps: int
    mirror: bool


@dataclass
class CanvasSettings:
    width: int
    height: int
    background_color: str


@dataclass
class PenSettings:
    color: str
    width: int
    opacity: float


@dataclass
class TrackingSettings:
    min_detection_confidence: float
    pinch_down_threshold: float
    pinch_up_threshold: float
    stable_frames: int
    lost_frame_limit: int


@dataclass
class FilterSettings:
    type: str
    strength: float


@dataclass
class AppSettings:
    camera: CameraSettings
    canvas: CanvasSettings
    pen: PenSettings
    tracking: TrackingSettings
    filter: FilterSettings

    @classmethod
    def defaults(cls) -> "AppSettings":
        return cls.from_dict(default_settings_payload())

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "AppSettings":
        camera = payload["camera"]
        canvas = payload["canvas"]
        pen = payload["pen"]
        tracking = payload["tracking"]
        filter_settings = payload["filter"]

        return cls(
            camera=CameraSettings(**camera),
            canvas=CanvasSettings(**canvas),
            pen=PenSettings(**pen),
            tracking=TrackingSettings(**tracking),
            filter=FilterSettings(**filter_settings),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class SettingsManager:
    def __init__(self, paths: AppPaths, config_filename: str = "config.json") -> None:
        self.paths = paths
        self.config_path = paths.config_dir / config_filename

    def load(self) -> AppSettings:
        self._ensure_directories()

        try:
            payload = json.loads(self.config_path.read_text(encoding="utf-8"))
            settings = AppSettings.from_dict(payload)
        except (FileNotFoundError, JSONDecodeError, KeyError, TypeError):
            settings = AppSettings.defaults()
            self.save(settings)

        return settings

    def save(self, settings: AppSettings) -> None:
        self._ensure_directories()
        self.config_path.write_text(
            json.dumps(settings.to_dict(), indent=2),
            encoding="utf-8",
        )

    def _ensure_directories(self) -> None:
        for directory in (self.paths.config_dir, self.paths.data_dir, self.paths.log_dir):
            Path(directory).mkdir(parents=True, exist_ok=True)
