from __future__ import annotations

import numpy as np
import threading
import time

from airwrite.app import AirWriteApp
from airwrite.devices.camera_source import CameraFrame, CameraSource
from airwrite.tracking.landmarks import HandLandmarks, Point2D


class StubCameraSource(CameraSource):
    def __init__(self, camera_index: int) -> None:
        self.camera_index = camera_index
        self.closed = False

    def frames(self):
        yield CameraFrame(
            data=np.full((6, 10, 3), self.camera_index, dtype=np.uint8),
            index=0,
        )

    def close(self) -> None:
        self.closed = True


def test_app_process_frame_updates_camera_preview_from_camera_source(
    tmp_path, monkeypatch, qtbot
):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))
    created_indexes: list[int] = []

    def camera_source_factory(camera_settings):
        created_indexes.append(camera_settings.index)
        return StubCameraSource(camera_settings.index)

    app = AirWriteApp.for_test(camera_source_factory=camera_source_factory)
    qtbot.addWidget(app.window)

    app._process_frame()

    pixmap = app.window.camera_preview.preview_label.pixmap()
    assert created_indexes == [0]
    assert pixmap is not None
    assert not pixmap.isNull()


def test_app_recreates_camera_source_when_camera_index_changes(
    tmp_path, monkeypatch, qtbot
):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))
    created_sources: list[StubCameraSource] = []

    def camera_source_factory(camera_settings):
        source = StubCameraSource(camera_settings.index)
        created_sources.append(source)
        return source

    app = AirWriteApp.for_test(camera_source_factory=camera_source_factory)
    qtbot.addWidget(app.window)

    app._process_frame()
    app.window.settings_panel.camera_index_spinbox.setValue(3)
    app._process_frame()

    assert [source.camera_index for source in created_sources] == [0, 3]
    assert created_sources[0].closed is True


def test_app_process_frame_does_not_block_on_slow_camera_source(
    tmp_path, monkeypatch, qtbot
):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))

    class SlowCameraSource(CameraSource):
        def frames(self):
            time.sleep(0.2)
            yield CameraFrame(data=np.zeros((6, 10, 3), dtype=np.uint8), index=0)

    app = AirWriteApp.for_test(camera_source_factory=lambda _settings: SlowCameraSource())
    qtbot.addWidget(app.window)

    started_at = time.perf_counter()
    app._process_frame()
    elapsed = time.perf_counter() - started_at

    assert elapsed < 0.1


def test_app_throttles_camera_reopen_after_failure(tmp_path, monkeypatch, qtbot):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))
    attempts = 0

    def failing_factory(_settings):
        nonlocal attempts
        attempts += 1
        raise RuntimeError("camera unavailable")

    app = AirWriteApp.for_test(camera_source_factory=failing_factory)
    qtbot.addWidget(app.window)

    app._process_frame()
    app._process_frame()

    assert attempts == 1


def test_old_camera_reader_cannot_overwrite_new_camera_session(
    tmp_path, monkeypatch, qtbot
):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))
    old_session_gate = threading.Event()
    new_session_gate = threading.Event()

    class DeferredCameraSource(CameraSource):
        def __init__(self, camera_index: int, gate: threading.Event, frame_width: int) -> None:
            self.camera_index = camera_index
            self.gate = gate
            self.frame_width = frame_width

        def frames(self):
            self.gate.wait(timeout=2.0)
            yield CameraFrame(
                data=np.full((6, self.frame_width, 3), self.camera_index, dtype=np.uint8),
                index=0,
            )

        def close(self) -> None:
            return None

    class ContinuousCameraSource(CameraSource):
        def __init__(self, camera_index: int, gate: threading.Event, frame_width: int) -> None:
            self.camera_index = camera_index
            self.gate = gate
            self.frame_width = frame_width

        def frames(self):
            self.gate.wait(timeout=2.0)
            frame = CameraFrame(
                data=np.full((6, self.frame_width, 3), self.camera_index, dtype=np.uint8),
                index=0,
            )
            while True:
                yield frame
                time.sleep(0.01)

        def close(self) -> None:
            return None

    def camera_source_factory(camera_settings):
        if camera_settings.index == 0:
            return DeferredCameraSource(0, old_session_gate, frame_width=10)
        return ContinuousCameraSource(3, new_session_gate, frame_width=20)

    app = AirWriteApp.for_test(camera_source_factory=camera_source_factory)
    qtbot.addWidget(app.window)

    app._process_frame()
    app.window.settings_panel.camera_index_spinbox.setValue(3)
    app._process_frame()

    new_session_gate.set()
    qtbot.waitUntil(
        lambda: (
            app._process_frame() is None
            or True
        )
        and app.window.camera_preview.preview_label.pixmap() is not None
        and not app.window.camera_preview.preview_label.pixmap().isNull(),
        timeout=2000,
    )
    new_session_image = app.window.camera_preview.preview_label.pixmap().toImage()
    expected_color = new_session_image.pixelColor(
        new_session_image.width() // 2,
        new_session_image.height() // 2,
    )

    old_session_gate.set()
    for _ in range(10):
        app._process_frame()
        qtbot.wait(10)

    final_image = app.window.camera_preview.preview_label.pixmap().toImage()
    assert final_image.pixelColor(
        final_image.width() // 2,
        final_image.height() // 2,
    ) == expected_color


def test_app_draws_from_hand_tracking_and_updates_metrics(
    tmp_path, monkeypatch, qtbot
):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))

    class ContinuousStubCameraSource(CameraSource):
        def frames(self):
            frame = CameraFrame(data=np.full((120, 160, 3), 127, dtype=np.uint8), index=0)
            while True:
                yield frame
                time.sleep(0.01)

    sequence = iter(
        [
            HandLandmarks(
                index_tip=Point2D(0.50, 0.50),
                thumb_tip=Point2D(0.50, 0.50),
                wrist=Point2D(0.10, 0.10),
                middle_mcp=Point2D(0.20, 0.10),
                confidence=0.92,
            ),
            HandLandmarks(
                index_tip=Point2D(0.52, 0.50),
                thumb_tip=Point2D(0.50, 0.50),
                wrist=Point2D(0.10, 0.10),
                middle_mcp=Point2D(0.20, 0.10),
                confidence=0.92,
            ),
            HandLandmarks(
                index_tip=Point2D(0.60, 0.52),
                thumb_tip=Point2D(0.50, 0.50),
                wrist=Point2D(0.10, 0.10),
                middle_mcp=Point2D(0.20, 0.10),
                confidence=0.92,
            ),
        ]
    )
    last_landmarks = HandLandmarks(
        index_tip=Point2D(0.60, 0.52),
        thumb_tip=Point2D(0.50, 0.50),
        wrist=Point2D(0.10, 0.10),
        middle_mcp=Point2D(0.20, 0.10),
        confidence=0.92,
    )

    def hand_landmark_provider(_frame):
        nonlocal last_landmarks
        try:
            last_landmarks = next(sequence)
        except StopIteration:
            return last_landmarks
        return last_landmarks

    app = AirWriteApp.for_test(
        camera_source_factory=lambda _settings: ContinuousStubCameraSource(),
        hand_landmark_provider=hand_landmark_provider,
    )
    qtbot.addWidget(app.window)
    app.settings.tracking.gesture_stable_frames = 1
    app.settings.filter.deadzone = 0.0
    app.settings.filter.strength = 0.0
    app._rebuild_interaction_pipeline()
    app.window.resize(800, 600)
    app.window.show()

    qtbot.waitUntil(
        lambda: (app._process_frame() is None or True) and len(app.window.canvas.points) >= 1,
        timeout=2000,
    )

    assert len(app.window.canvas.points) >= 1
    assert "Drawing: active" in app.window.status_bar_widget._metrics_label.text()
    assert "FPS: --" not in app.window.status_bar_widget._metrics_label.text()
    assert "Latency: --" not in app.window.status_bar_widget._metrics_label.text()
    assert "Confidence: 0.92" in app.window.status_bar_widget._metrics_label.text()
