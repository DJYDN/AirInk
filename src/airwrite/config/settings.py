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

    def __post_init__(self) -> None:
        _require_non_negative_int("camera.index", self.index)
        _require_positive_int("camera.width", self.width)
        _require_positive_int("camera.height", self.height)
        _require_positive_int("camera.fps", self.fps)
        _require_bool("camera.mirror", self.mirror)


@dataclass
class CanvasSettings:
    width: int
    height: int
    background_color: str

    def __post_init__(self) -> None:
        _require_positive_int("canvas.width", self.width)
        _require_positive_int("canvas.height", self.height)
        _require_non_empty_str("canvas.background_color", self.background_color)


@dataclass
class PenSettings:
    color: str
    width: int
    opacity: float

    def __post_init__(self) -> None:
        _require_non_empty_str("pen.color", self.color)
        _require_positive_int("pen.width", self.width)
        _require_number_in_range("pen.opacity", self.opacity, minimum=0.0, maximum=1.0)


@dataclass
class TrackingSettings:
    min_detection_confidence: float
    pinch_down_threshold: float
    pinch_up_threshold: float
    stable_frames: int
    lost_frame_limit: int

    def __post_init__(self) -> None:
        _require_number_in_range(
            "tracking.min_detection_confidence",
            self.min_detection_confidence,
            minimum=0.0,
            maximum=1.0,
        )
        _require_number_in_range(
            "tracking.pinch_down_threshold",
            self.pinch_down_threshold,
            minimum=0.0,
            maximum=1.0,
        )
        _require_number_in_range(
            "tracking.pinch_up_threshold",
            self.pinch_up_threshold,
            minimum=0.0,
            maximum=1.0,
        )
        _require_positive_int("tracking.stable_frames", self.stable_frames)
        _require_positive_int("tracking.lost_frame_limit", self.lost_frame_limit)


@dataclass
class FilterSettings:
    type: str
    strength: float

    def __post_init__(self) -> None:
        _require_non_empty_str("filter.type", self.type)
        _require_number_in_range("filter.strength", self.strength, minimum=0.0, maximum=1.0)


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
        except (FileNotFoundError, JSONDecodeError, KeyError, TypeError, ValueError):
            settings = AppSettings.defaults()
            self.save(settings)

        return settings

    def save(self, settings: AppSettings) -> None:
        self._ensure_directories()
        validated_settings = AppSettings.from_dict(settings.to_dict())
        self.config_path.write_text(
            json.dumps(validated_settings.to_dict(), indent=2),
            encoding="utf-8",
        )

    def _ensure_directories(self) -> None:
        for directory in (self.paths.config_dir, self.paths.data_dir, self.paths.log_dir):
            Path(directory).mkdir(parents=True, exist_ok=True)


def _require_bool(name: str, value: object) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")


def _require_non_empty_str(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_non_negative_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _require_positive_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _require_number_in_range(
    name: str,
    value: object,
    *,
    minimum: float,
    maximum: float,
) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")

    if value < minimum or value > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
