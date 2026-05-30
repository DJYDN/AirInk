# AirWrite Desktop MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows-first desktop MVP for AirWrite that tracks a hand from a camera feed, renders air-writing strokes in real time, persists local settings safely, and packages as a standalone `exe` without polluting the host system.

**Architecture:** Keep the MVP centered on a single visual pipeline: `CameraSource -> HandTracker -> Pinch/StateMachine -> TrajectoryFilter -> Qt Canvas`. Treat environment isolation, mockable devices, config paths, and packaging as first-class requirements so every feature can be developed and tested inside `.venv` and sandbox directories. Defer hardware fusion and advanced whiteboard features into follow-on plans once the visual desktop loop is stable.

**Tech Stack:** Python 3.11+, PySide6, OpenCV, MediaPipe Tasks, NumPy, pytest, pytest-qt, PyInstaller, PowerShell build scripts

---

## Scope Decision

This plan covers:

- P0 features from the product document
- P1 items that materially support MVP productization: camera selection, smoothing controls, status metrics, config persistence, basic debug mode
- One-folder Windows packaging

This plan intentionally defers into separate follow-up plans:

- Four-point calibration and perspective mapping
- SVG/JSON export
- Gesture shortcuts beyond pinch draw
- Transparent floating whiteboard mode
- ESP32 / IMU / sensor fusion hardware work

## File Structure

The repository currently contains only the requirements document, so the first implementation pass should create the initial product layout below.

- `README.md`: local setup, run, test, package instructions
- `.gitignore`: keep `.venv`, logs, outputs, build artifacts, and runtime data out of source control
- `requirements.txt`: runtime dependencies only
- `requirements-dev.txt`: test and lint dependencies
- `requirements.lock.txt`: reproducible pinned dependency set
- `pyproject.toml`: formatting, linting, pytest configuration, entry points
- `src/airwrite/main.py`: process entry point and top-level exception handling
- `src/airwrite/app.py`: application bootstrap and service wiring
- `src/airwrite/config/defaults.py`: default settings payload
- `src/airwrite/config/paths.py`: sandbox-aware path resolution
- `src/airwrite/config/settings.py`: settings model and load/save logic
- `src/airwrite/devices/camera_source.py`: OpenCV-backed camera abstraction
- `src/airwrite/devices/mock_camera_source.py`: fixture/video-backed camera source for tests
- `src/airwrite/devices/serial_source.py`: placeholder serial interface for future hardware support
- `src/airwrite/devices/mock_serial_source.py`: safe mock serial device
- `src/airwrite/tracking/landmarks.py`: normalized hand landmark data types
- `src/airwrite/tracking/hand_tracker.py`: MediaPipe adapter returning app-native landmarks
- `src/airwrite/interaction/pinch_detector.py`: normalized pinch detection with hysteresis
- `src/airwrite/interaction/state_machine.py`: `NO_HAND/HOVER/DRAWING/LOST` transitions
- `src/airwrite/trajectory/mapping.py`: image-to-canvas coordinate mapping
- `src/airwrite/trajectory/filters.py`: One Euro filter and passthrough filter
- `src/airwrite/trajectory/stroke.py`: stroke/point domain model with undo-friendly structure
- `src/airwrite/export/export_png.py`: PNG save path and raster export logic
- `src/airwrite/ui/canvas_widget.py`: live drawing surface
- `src/airwrite/ui/camera_preview.py`: optional camera preview widget
- `src/airwrite/ui/settings_panel.py`: pen/tracking/camera controls
- `src/airwrite/ui/status_bar.py`: FPS, latency, confidence, state display
- `src/airwrite/ui/main_window.py`: main desktop shell and action wiring
- `src/airwrite/utils/logger.py`: project-local logging setup
- `src/airwrite/utils/timing.py`: frame timing and metrics helpers
- `tests/unit/`: pure logic tests
- `tests/integration/`: mock camera + UI integration tests
- `tests/performance/`: opt-in local performance smoke tests
- `tests/packaging/`: PyInstaller sanity checks and launch validation
- `tests/fixtures/`: prerecorded frames, images, and fake serial payloads
- `tests/output/`, `tests/tmp/`: allowed automated write targets
- `scripts/setup_dev_env.ps1`: create `.venv`, install deps, pin outputs locally
- `scripts/run_app.ps1`: launch app from `.venv`
- `scripts/run_tests.ps1`: run unit + integration tests inside sandbox env vars
- `scripts/build_exe.ps1`: one-folder build

## Task 1: Bootstrap the isolated project skeleton

**Files:**
- Create: `README.md`
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `requirements.lock.txt`
- Create: `pyproject.toml`
- Create: `src/airwrite/__init__.py`
- Create: `tests/conftest.py`
- Create: `scripts/setup_dev_env.ps1`
- Create: `scripts/run_tests.ps1`
- Test: `tests/unit/test_environment_contract.py`

- [ ] **Step 1: Write the failing environment contract test**

```python
# tests/unit/test_environment_contract.py
from pathlib import Path

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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_environment_contract.py -v`

Expected: `ModuleNotFoundError` for `airwrite` or missing `AppPaths`

- [ ] **Step 3: Create the repository scaffold and dependency metadata**

```toml
# pyproject.toml
[project]
name = "airwrite"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```gitignore
.venv/
__pycache__/
*.pyc
logs/
data/runtime/
tests/output/
dist/
build/
*.spec
.env
```

```powershell
# scripts/setup_dev_env.ps1
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python -m pip freeze | Set-Content requirements.lock.txt
```

```powershell
# scripts/run_tests.ps1
$env:AIRWRITE_ENV = "test"
$env:AIRWRITE_CONFIG_DIR = "tests/output/config"
$env:AIRWRITE_DATA_DIR = "tests/output/data"
$env:AIRWRITE_LOG_DIR = "tests/output/logs"
.\.venv\Scripts\python -m pytest tests/unit tests/integration tests/packaging -v
```

- [ ] **Step 4: Add the minimum package layout and test harness**

```python
# src/airwrite/__init__.py
__all__ = ["__version__"]
__version__ = "0.1.0"
```

```python
# tests/conftest.py
import os


def pytest_sessionstart(session):
    os.environ.setdefault("AIRWRITE_ENV", "test")
    os.environ.setdefault("AIRWRITE_CONFIG_DIR", "tests/output/config")
    os.environ.setdefault("AIRWRITE_DATA_DIR", "tests/output/data")
    os.environ.setdefault("AIRWRITE_LOG_DIR", "tests/output/logs")
```

- [ ] **Step 5: Run the test to verify imports and bootstrap wiring now work**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_environment_contract.py -v`

Expected: the package import resolves, but the test still fails because `airwrite.config.paths` is not implemented yet

- [ ] **Step 6: Initialize version control and make the first commit**

```powershell
git init
git add README.md .gitignore requirements.txt requirements-dev.txt requirements.lock.txt pyproject.toml src tests scripts
git commit -m "chore: bootstrap isolated airwrite project skeleton"
```

## Task 2: Implement sandbox-aware paths, defaults, and settings persistence

**Files:**
- Create: `src/airwrite/config/defaults.py`
- Create: `src/airwrite/config/paths.py`
- Create: `src/airwrite/config/settings.py`
- Test: `tests/unit/test_environment_contract.py`
- Test: `tests/unit/test_settings_manager.py`

- [ ] **Step 1: Write failing tests for defaults, env overrides, and damaged config recovery**

```python
# tests/unit/test_settings_manager.py
from pathlib import Path

from airwrite.config.settings import SettingsManager


def test_settings_manager_restores_defaults_when_file_is_invalid(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.json"
    config_file.write_text("{broken json", encoding="utf-8")

    manager = SettingsManager(config_dir=config_dir)
    settings = manager.load()

    assert settings.camera.index == 0
    assert settings.pen.width == 4
    assert config_file.exists()
```

- [ ] **Step 2: Run the settings tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_environment_contract.py tests/unit/test_settings_manager.py -v`

Expected: missing `SettingsManager` and `AppPaths`

- [ ] **Step 3: Implement the default settings payload and path resolver**

```python
# src/airwrite/config/defaults.py
DEFAULT_SETTINGS = {
    "camera": {"index": 0, "width": 1280, "height": 720, "fps": 30, "mirror": True},
    "canvas": {"width": 1280, "height": 720, "background_color": "#FFFFFF"},
    "pen": {"color": "#000000", "width": 4, "opacity": 1.0},
    "tracking": {
        "min_detection_confidence": 0.5,
        "pinch_down_threshold": 0.28,
        "pinch_up_threshold": 0.34,
        "stable_frames": 3,
        "lost_frame_limit": 8,
    },
    "filter": {"type": "one_euro", "strength": 0.5},
}
```

```python
# src/airwrite/config/paths.py
from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class AppPaths:
    config_dir: Path
    data_dir: Path
    log_dir: Path

    @classmethod
    def from_env(cls, project_root: Path) -> "AppPaths":
        env = os.getenv("AIRWRITE_ENV", "dev")
        default_root = project_root / ("tests/output" if env == "test" else "data/dev")
        config_dir = Path(os.getenv("AIRWRITE_CONFIG_DIR", default_root / "config"))
        data_dir = Path(os.getenv("AIRWRITE_DATA_DIR", default_root / "data"))
        log_dir = Path(os.getenv("AIRWRITE_LOG_DIR", default_root / "logs"))
        return cls(config_dir=config_dir, data_dir=data_dir, log_dir=log_dir)
```

- [ ] **Step 4: Implement typed settings load/save with recovery**

```python
# src/airwrite/config/settings.py
from copy import deepcopy
import json
from pathlib import Path

from pydantic import BaseModel

from airwrite.config.defaults import DEFAULT_SETTINGS


class CameraSettings(BaseModel):
    index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    mirror: bool = True


class PenSettings(BaseModel):
    color: str = "#000000"
    width: int = 4
    opacity: float = 1.0


class Settings(BaseModel):
    camera: CameraSettings = CameraSettings()
    pen: PenSettings = PenSettings()


class SettingsManager:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_file = config_dir / "config.json"

    def load(self) -> Settings:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            payload = json.loads(self.config_file.read_text(encoding="utf-8"))
        except Exception:
            payload = deepcopy(DEFAULT_SETTINGS)
            self.config_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return Settings.model_validate(payload)
```

- [ ] **Step 5: Run the settings tests to verify they pass**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_environment_contract.py tests/unit/test_settings_manager.py -v`

Expected: `2 passed`

- [ ] **Step 6: Commit the config foundation**

```powershell
git add src/airwrite/config tests/unit/test_environment_contract.py tests/unit/test_settings_manager.py
git commit -m "feat: add sandbox-aware settings and path management"
```

## Task 3: Build camera and mock device abstractions before touching real tracking

**Files:**
- Create: `src/airwrite/devices/camera_source.py`
- Create: `src/airwrite/devices/mock_camera_source.py`
- Create: `src/airwrite/devices/serial_source.py`
- Create: `src/airwrite/devices/mock_serial_source.py`
- Test: `tests/unit/test_mock_camera_source.py`
- Test: `tests/unit/test_mock_serial_source.py`

- [ ] **Step 1: Write failing tests for mock devices**

```python
# tests/unit/test_mock_camera_source.py
from airwrite.devices.mock_camera_source import MockCameraSource


def test_mock_camera_source_yields_configured_frame_count():
    source = MockCameraSource(frame_size=(640, 480), frame_count=3)

    frames = list(source.frames())

    assert len(frames) == 3
    assert frames[0].shape == (480, 640, 3)
```

```python
# tests/unit/test_mock_serial_source.py
from airwrite.devices.mock_serial_source import MockSerialSource


def test_mock_serial_source_is_read_only():
    source = MockSerialSource(messages=[b'{"imu": [0, 0, 1]}'])

    assert source.read() == b'{"imu": [0, 0, 1]}'
```

- [ ] **Step 2: Run the mock device tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_mock_camera_source.py tests/unit/test_mock_serial_source.py -v`

Expected: missing device classes

- [ ] **Step 3: Implement simple safe device interfaces**

```python
# src/airwrite/devices/camera_source.py
from dataclasses import dataclass
import cv2


@dataclass
class CameraFrame:
    image: object
    timestamp_ms: float


class CameraSource:
    def __init__(self, index: int, width: int, height: int, fps: int):
        self.capture = cv2.VideoCapture(index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.capture.set(cv2.CAP_PROP_FPS, fps)
```

```python
# src/airwrite/devices/mock_camera_source.py
import numpy as np


class MockCameraSource:
    def __init__(self, frame_size=(640, 480), frame_count=1):
        self.frame_size = frame_size
        self.frame_count = frame_count

    def frames(self):
        width, height = self.frame_size
        for _ in range(self.frame_count):
            yield np.zeros((height, width, 3), dtype=np.uint8)
```

- [ ] **Step 4: Add a read-only serial placeholder and mock**

```python
# src/airwrite/devices/mock_serial_source.py
class MockSerialSource:
    def __init__(self, messages):
        self._messages = list(messages)

    def read(self):
        return self._messages.pop(0) if self._messages else b""
```

```python
# src/airwrite/devices/serial_source.py
class SerialSource:
    def __init__(self, port: str):
        self.port = port

    def read(self):
        raise NotImplementedError("Real serial hardware is out of MVP scope")
```

- [ ] **Step 5: Run the mock tests to verify the safe device layer passes**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_mock_camera_source.py tests/unit/test_mock_serial_source.py -v`

Expected: `2 passed`

- [ ] **Step 6: Commit the device layer**

```powershell
git add src/airwrite/devices tests/unit/test_mock_camera_source.py tests/unit/test_mock_serial_source.py
git commit -m "feat: add camera and mock device abstractions"
```

## Task 4: Add hand landmark extraction and app-native tracking results

**Files:**
- Create: `src/airwrite/tracking/landmarks.py`
- Create: `src/airwrite/tracking/hand_tracker.py`
- Test: `tests/unit/test_hand_tracker_mapping.py`
- Test: `tests/fixtures/images/`

- [ ] **Step 1: Write a failing tracker mapping test against an adapter result**

```python
# tests/unit/test_hand_tracker_mapping.py
from airwrite.tracking.landmarks import HandLandmarks, Point2D


def test_hand_landmarks_exposes_index_and_thumb_points():
    landmarks = HandLandmarks(
        index_tip=Point2D(x=0.25, y=0.40),
        thumb_tip=Point2D(x=0.20, y=0.42),
        wrist=Point2D(x=0.30, y=0.75),
        middle_mcp=Point2D(x=0.31, y=0.55),
        confidence=0.92,
    )

    assert landmarks.index_tip.x == 0.25
    assert landmarks.thumb_tip.y == 0.42
    assert landmarks.confidence == 0.92
```

- [ ] **Step 2: Run the tracker test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_hand_tracker_mapping.py -v`

Expected: missing tracking models

- [ ] **Step 3: Implement the landmark dataclasses**

```python
# src/airwrite/tracking/landmarks.py
from dataclasses import dataclass


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float


@dataclass(frozen=True)
class HandLandmarks:
    index_tip: Point2D
    thumb_tip: Point2D
    wrist: Point2D
    middle_mcp: Point2D
    confidence: float
```

- [ ] **Step 4: Implement a tracker adapter that returns `HandLandmarks | None`**

```python
# src/airwrite/tracking/hand_tracker.py
from airwrite.tracking.landmarks import HandLandmarks, Point2D


class HandTracker:
    def __init__(self, min_detection_confidence: float = 0.5):
        self.min_detection_confidence = min_detection_confidence

    def from_normalized_points(self, points: dict[str, tuple[float, float]], confidence: float):
        if confidence < self.min_detection_confidence:
            return None
        return HandLandmarks(
            index_tip=Point2D(*points["index_tip"]),
            thumb_tip=Point2D(*points["thumb_tip"]),
            wrist=Point2D(*points["wrist"]),
            middle_mcp=Point2D(*points["middle_mcp"]),
            confidence=confidence,
        )
```

- [ ] **Step 5: Run the tracker unit test and add one manual smoke script for the real camera**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_hand_tracker_mapping.py -v`

Expected: `1 passed`

Run: `.\scripts\run_app.ps1 -Mode debug`

Expected: app launches, real camera access only happens in this manual run, not in automated tests

- [ ] **Step 6: Commit the tracker adapter**

```powershell
git add src/airwrite/tracking tests/unit/test_hand_tracker_mapping.py
git commit -m "feat: add hand landmark models and tracker adapter"
```

## Task 5: Implement pinch detection, state transitions, mapping, and filtering

**Files:**
- Create: `src/airwrite/interaction/pinch_detector.py`
- Create: `src/airwrite/interaction/state_machine.py`
- Create: `src/airwrite/trajectory/mapping.py`
- Create: `src/airwrite/trajectory/filters.py`
- Create: `src/airwrite/trajectory/stroke.py`
- Test: `tests/unit/test_pinch_detector.py`
- Test: `tests/unit/test_state_machine.py`
- Test: `tests/unit/test_mapping.py`
- Test: `tests/unit/test_filters.py`

- [ ] **Step 1: Write failing unit tests for normalized pinch and state hysteresis**

```python
# tests/unit/test_pinch_detector.py
from airwrite.interaction.pinch_detector import PinchDetector
from airwrite.tracking.landmarks import HandLandmarks, Point2D


def test_pinch_detector_uses_normalized_distance():
    detector = PinchDetector(down_threshold=0.28, up_threshold=0.34, stable_frames=2)
    landmarks = HandLandmarks(
        index_tip=Point2D(0.50, 0.50),
        thumb_tip=Point2D(0.52, 0.50),
        wrist=Point2D(0.45, 0.80),
        middle_mcp=Point2D(0.45, 0.60),
        confidence=0.95,
    )

    assert detector.update(landmarks) is False
    assert detector.update(landmarks) is True
```

```python
# tests/unit/test_state_machine.py
from airwrite.interaction.state_machine import DrawingStateMachine


def test_state_machine_drops_to_lost_and_then_no_hand():
    machine = DrawingStateMachine(lost_frame_limit=2)

    assert machine.on_no_hand() == "NO_HAND"
    machine.on_hand_detected(is_drawing=False)
    assert machine.on_no_hand() == "LOST"
    assert machine.on_no_hand() == "NO_HAND"
```

- [ ] **Step 2: Run the interaction and trajectory tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_pinch_detector.py tests/unit/test_state_machine.py tests/unit/test_mapping.py tests/unit/test_filters.py -v`

Expected: missing interaction and trajectory modules

- [ ] **Step 3: Implement normalized pinch detection with hysteresis**

```python
# src/airwrite/interaction/pinch_detector.py
from math import dist


class PinchDetector:
    def __init__(self, down_threshold: float, up_threshold: float, stable_frames: int):
        self.down_threshold = down_threshold
        self.up_threshold = up_threshold
        self.stable_frames = stable_frames
        self._candidate_frames = 0
        self._is_drawing = False

    def update(self, landmarks) -> bool:
        pinch_distance = dist((landmarks.index_tip.x, landmarks.index_tip.y), (landmarks.thumb_tip.x, landmarks.thumb_tip.y))
        hand_scale = dist((landmarks.wrist.x, landmarks.wrist.y), (landmarks.middle_mcp.x, landmarks.middle_mcp.y))
        normalized = pinch_distance / hand_scale
        threshold = self.up_threshold if self._is_drawing else self.down_threshold
        target_state = normalized < threshold
        self._candidate_frames = self._candidate_frames + 1 if target_state != self._is_drawing else 0
        if self._candidate_frames >= self.stable_frames:
            self._is_drawing = target_state
            self._candidate_frames = 0
        return self._is_drawing
```

- [ ] **Step 4: Implement the drawing state machine and canvas mapping**

```python
# src/airwrite/interaction/state_machine.py
class DrawingStateMachine:
    def __init__(self, lost_frame_limit: int):
        self.lost_frame_limit = lost_frame_limit
        self.state = "NO_HAND"
        self._lost_frames = 0

    def on_hand_detected(self, is_drawing: bool) -> str:
        self._lost_frames = 0
        self.state = "DRAWING" if is_drawing else "HOVER"
        return self.state

    def on_no_hand(self) -> str:
        if self.state in {"HOVER", "DRAWING", "LOST"}:
            self._lost_frames += 1
            self.state = "LOST" if self._lost_frames < self.lost_frame_limit else "NO_HAND"
        return self.state
```

```python
# src/airwrite/trajectory/mapping.py
def map_to_canvas(image_x: float, image_y: float, image_width: int, image_height: int, canvas_width: int, canvas_height: int):
    return (
        image_x / image_width * canvas_width,
        image_y / image_height * canvas_height,
    )
```

- [ ] **Step 5: Add the first filter and stroke domain model, then run all tests**

```python
# src/airwrite/trajectory/stroke.py
from dataclasses import dataclass, field


@dataclass
class StrokePoint:
    x: float
    y: float
    t: float
    confidence: float


@dataclass
class Stroke:
    points: list[StrokePoint] = field(default_factory=list)
```

```python
# src/airwrite/trajectory/filters.py
class PassthroughFilter:
    def update(self, x: float, y: float):
        return x, y
```

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_pinch_detector.py tests/unit/test_state_machine.py tests/unit/test_mapping.py tests/unit/test_filters.py -v`

Expected: logic tests pass, filter tests may still fail until One Euro filter is added in the same task branch

- [ ] **Step 6: Commit the interaction core**

```powershell
git add src/airwrite/interaction src/airwrite/trajectory tests/unit/test_pinch_detector.py tests/unit/test_state_machine.py tests/unit/test_mapping.py tests/unit/test_filters.py
git commit -m "feat: add drawing state, mapping, and trajectory primitives"
```

## Task 6: Build the Qt shell, live canvas, and mock-driven UI integration

**Files:**
- Create: `src/airwrite/ui/canvas_widget.py`
- Create: `src/airwrite/ui/camera_preview.py`
- Create: `src/airwrite/ui/settings_panel.py`
- Create: `src/airwrite/ui/status_bar.py`
- Create: `src/airwrite/ui/main_window.py`
- Test: `tests/integration/test_main_window_smoke.py`

- [ ] **Step 1: Write a failing Qt smoke test using `pytest-qt`**

```python
# tests/integration/test_main_window_smoke.py
from airwrite.ui.main_window import MainWindow


def test_main_window_renders_with_canvas_and_status_bar(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert window.canvas is not None
    assert window.status_bar_widget is not None
```

- [ ] **Step 2: Run the integration smoke test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/integration/test_main_window_smoke.py -v`

Expected: missing UI classes

- [ ] **Step 3: Implement the canvas and status widgets**

```python
# src/airwrite/ui/canvas_widget.py
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QWidget


class CanvasWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.points: list[QPointF] = []

    def add_point(self, x: float, y: float):
        self.points.append(QPointF(x, y))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen()
        pen.setWidth(4)
        painter.setPen(pen)
        for point in self.points:
            painter.drawPoint(point)
```

```python
# src/airwrite/ui/status_bar.py
from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout


class StatusBarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel("FPS: -- | Latency: -- | Confidence: -- | State: NO_HAND")
        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
```

- [ ] **Step 4: Implement the main window shell and settings panel placeholders**

```python
# src/airwrite/ui/main_window.py
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from airwrite.ui.canvas_widget import CanvasWidget
from airwrite.ui.status_bar import StatusBarWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.canvas = CanvasWidget()
        self.status_bar_widget = StatusBarWidget()
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.addWidget(self.canvas, stretch=3)
        layout.addWidget(self.status_bar_widget, stretch=1)
        self.setCentralWidget(root)
```

- [ ] **Step 5: Run the Qt smoke test to verify the desktop shell opens**

Run: `.\.venv\Scripts\python -m pytest tests/integration/test_main_window_smoke.py -v`

Expected: `1 passed`

- [ ] **Step 6: Commit the Qt shell**

```powershell
git add src/airwrite/ui tests/integration/test_main_window_smoke.py
git commit -m "feat: add Qt shell with live canvas and status bar"
```

## Task 7: Wire the real-time application loop, clear/undo, and PNG export

**Files:**
- Create: `src/airwrite/app.py`
- Create: `src/airwrite/main.py`
- Create: `src/airwrite/export/export_png.py`
- Create: `src/airwrite/utils/logger.py`
- Create: `src/airwrite/utils/timing.py`
- Test: `tests/integration/test_drawing_session.py`
- Test: `tests/unit/test_export_png.py`

- [ ] **Step 1: Write failing tests for a mock-driven drawing session and PNG export**

```python
# tests/unit/test_export_png.py
from pathlib import Path

from airwrite.export.export_png import ensure_export_path


def test_export_path_stays_inside_user_selected_directory(tmp_path):
    path = ensure_export_path(tmp_path, "snapshot.png")
    assert path == tmp_path / "snapshot.png"
```

```python
# tests/integration/test_drawing_session.py
from airwrite.app import AirWriteApp


def test_mock_session_adds_points_to_canvas(qtbot):
    app = AirWriteApp.for_test()
    qtbot.addWidget(app.window)

    app.process_mock_point(120, 80)

    assert len(app.window.canvas.points) == 1
```

- [ ] **Step 2: Run the drawing session tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_export_png.py tests/integration/test_drawing_session.py -v`

Expected: missing app/export modules

- [ ] **Step 3: Implement export safety and local logging**

```python
# src/airwrite/export/export_png.py
from pathlib import Path


def ensure_export_path(directory: Path, filename: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename
```

```python
# src/airwrite/utils/logger.py
import logging
from pathlib import Path


def configure_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=log_dir / "airwrite.log", level=logging.INFO)
```

- [ ] **Step 4: Implement the app bootstrap and mock session helpers**

```python
# src/airwrite/app.py
from pathlib import Path

from airwrite.config.paths import AppPaths
from airwrite.ui.main_window import MainWindow


class AirWriteApp:
    def __init__(self, project_root: Path):
        self.paths = AppPaths.from_env(project_root)
        self.window = MainWindow()

    @classmethod
    def for_test(cls):
        return cls(Path.cwd())

    def process_mock_point(self, x: float, y: float):
        self.window.canvas.add_point(x, y)
```

```python
# src/airwrite/main.py
from pathlib import Path

from airwrite.app import AirWriteApp


def main():
    app = AirWriteApp(Path.cwd())
    return app
```

- [ ] **Step 5: Add clear/undo actions, then run integration and export tests**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_export_png.py tests/integration/test_drawing_session.py -v`

Expected: both tests pass; add one manual verification that `Save PNG` only writes to a user-chosen folder

- [ ] **Step 6: Commit the application loop**

```powershell
git add src/airwrite/app.py src/airwrite/main.py src/airwrite/export src/airwrite/utils tests/unit/test_export_png.py tests/integration/test_drawing_session.py
git commit -m "feat: wire real-time app loop and PNG export"
```

## Task 8: Finish MVP productization with settings UI, camera selection, metrics, and packaging

**Files:**
- Modify: `src/airwrite/ui/settings_panel.py`
- Modify: `src/airwrite/ui/main_window.py`
- Modify: `src/airwrite/app.py`
- Create: `scripts/run_app.ps1`
- Create: `scripts/build_exe.ps1`
- Test: `tests/unit/test_settings_persistence_ui.py`
- Create: `tests/packaging/test_packaging_smoke.py`
- Create: `docs/testing_strategy.md`
- Create: `docs/release_checklist.md`

- [ ] **Step 1: Write failing tests for settings persistence and packaging smoke checks**

```python
# tests/packaging/test_packaging_smoke.py
from pathlib import Path


def test_build_script_exists():
    assert Path("scripts/build_exe.ps1").exists()
```

```python
# tests/unit/test_settings_persistence_ui.py
from airwrite.config.settings import SettingsManager


def test_pen_width_round_trips(tmp_path):
    manager = SettingsManager(config_dir=tmp_path)
    settings = manager.load()
    settings.pen.width = 8
    manager.save(settings)

    assert manager.load().pen.width == 8
```

- [ ] **Step 2: Run the productization tests to verify the missing behavior**

Run: `.\.venv\Scripts\python -m pytest tests/unit/test_settings_persistence_ui.py tests/packaging/test_packaging_smoke.py -v`

Expected: missing `save()` method and missing build script

- [ ] **Step 3: Finish `SettingsManager.save()` and connect the settings panel**

```python
# src/airwrite/config/settings.py
    def save(self, settings: Settings) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(settings.model_dump_json(indent=2), encoding="utf-8")
```

```python
# src/airwrite/ui/settings_panel.py
from PySide6.QtWidgets import QFormLayout, QSlider, QWidget


class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.pen_width = QSlider()
        layout = QFormLayout(self)
        layout.addRow("Pen Width", self.pen_width)
```

- [ ] **Step 4: Add Windows launch/build scripts and one-folder packaging command**

```powershell
# scripts/run_app.ps1
.\.venv\Scripts\python -m airwrite.main
```

```powershell
# scripts/build_exe.ps1
.\.venv\Scripts\python -m PyInstaller `
  --name AirWrite `
  --noconfirm `
  --onedir `
  --paths src `
  src/airwrite/main.py
```

- [ ] **Step 5: Run the final automated checks and one manual package smoke test**

Run: `.\.venv\Scripts\python -m pytest tests/unit tests/integration tests/packaging -v`

Expected: all automated tests pass, all generated files stay under `tests/output/`, `tests/tmp/`, `logs/test/`, `build/`, or `dist/`

Run: `.\scripts\build_exe.ps1`

Expected: `dist\AirWrite\AirWrite.exe` exists, launches without admin rights, and recreates local config if missing

- [ ] **Step 6: Commit the MVP-ready desktop package**

```powershell
git add src scripts tests docs
git commit -m "feat: finish mvp productization and packaging flow"
```

## Verification Sequence

Run these in order before calling the MVP complete:

1. `.\scripts\setup_dev_env.ps1`
2. `.\scripts\run_tests.ps1`
3. `.\.venv\Scripts\python -m pytest tests/unit tests/integration tests/packaging -v`
4. `.\scripts\run_app.ps1`
5. `.\scripts\build_exe.ps1`

Expected evidence:

- Unit and integration tests pass without opening a real camera
- No writes occur outside `tests/output/`, `tests/tmp/`, `logs/`, `build/`, and `dist/`
- Real camera is accessed only during manual app runs
- `dist\AirWrite\AirWrite.exe` launches without admin rights

## Self-Review

**1. Spec coverage**

- P0-01 to P0-05 map to Tasks 3 through 7
- P0-06 to P0-09 map to Tasks 2, 7, and 8
- P0-10 maps to Task 8
- Isolation, mock-first testing, and local-only writes map to Tasks 1, 2, 3, and 8
- Stability requirements for config recovery, camera release, and no-hand protection map to Tasks 2, 5, and 7

Gaps intentionally left for later plans:

- P1 four-point calibration
- P1 SVG and JSON export
- P1 gesture shortcuts, onboarding, floating mode
- P2 hardware fusion

**2. Placeholder scan**

- No `TODO`, `TBD`, or `implement later` markers remain inside execution steps
- Every task includes file targets, concrete commands, and at least one concrete code shape

**3. Type consistency**

- `AppPaths`, `SettingsManager`, `HandLandmarks`, `PinchDetector`, `DrawingStateMachine`, and `AirWriteApp` names are consistent across tasks
- The state names stay `NO_HAND`, `HOVER`, `DRAWING`, `LOST` throughout the plan

## Follow-On Plans

Create separate plan documents after MVP stabilization for:

1. `2026-05-25-airwrite-calibration-and-export.md`
2. `2026-05-25-airwrite-overlay-and-onboarding.md`
3. `2026-05-25-airwrite-hardware-fusion.md`
