from __future__ import annotations

import time

import numpy as np

import airwrite.app as app_module
from airwrite.app import AirWriteApp
from airwrite.devices.camera_source import CameraFrame, CameraSource
from airwrite.tracking.landmarks import HandLandmarks, Point2D
from airwrite.tracking.pen_pose import PenPose


class ContinuousStubCameraSource(CameraSource):
    def frames(self):
        frame = CameraFrame(data=np.full((120, 160, 3), 127, dtype=np.uint8), index=0)
        while True:
            yield frame
            time.sleep(0.01)


def test_app_collects_multi_stroke_session_and_keeps_candidates_until_confirmation(
    tmp_path, monkeypatch, qtbot
):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))

    sequence = iter(
        [
            _make_landmarks(index_tip=(0.50, 0.68)),
            _make_landmarks(index_tip=(0.50, 0.22)),
            _make_landmarks(index_tip=(0.56, 0.24)),
            _make_landmarks(index_tip=(0.50, 0.68)),
            _make_landmarks(index_tip=(0.50, 0.22)),
            _make_landmarks(index_tip=(0.60, 0.22)),
            _make_landmarks(index_tip=(0.50, 0.68)),
        ]
    )
    last_landmarks = _make_landmarks(index_tip=(0.50, 0.68))

    def hand_landmark_provider(_frame):
        nonlocal last_landmarks
        try:
            last_landmarks = next(sequence)
        except StopIteration:
            return last_landmarks
        return last_landmarks

    class StubOcrProvider:
        def recognize(self, _image, *, stroke_count: int) -> list[str]:
            return [f"candidate-{stroke_count}", "fallback"]

    app = AirWriteApp.for_test(
        camera_source_factory=lambda _settings: ContinuousStubCameraSource(),
        hand_landmark_provider=hand_landmark_provider,
        ocr_provider=StubOcrProvider(),
    )
    qtbot.addWidget(app.window)
    app.settings.tracking.gesture_stable_frames = 1
    app.settings.tracking.landmark_smoothing = 1.0
    app.settings.tracking.session_idle_timeout_ms = 20
    app.settings.filter.deadzone = 0.0
    app.settings.filter.strength = 0.0
    app.settings.filter.start_threshold = 0.0
    app._rebuild_interaction_pipeline()
    app.window.show()

    qtbot.waitUntil(
        lambda: (
            app._process_frame() is None
            or True
        ) and len(app._session_controller.session.strokes) >= 2,
        timeout=2000,
    )

    qtbot.waitUntil(
        lambda: (
            app._process_frame() is None
            or True
        ) and app.window.ocr_panel.candidate_texts() == ["candidate-2", "fallback"],
        timeout=2000,
    )

    assert len(app._session_controller.session.strokes) == 2
    assert app.window.ocr_panel.candidate_texts() == ["candidate-2", "fallback"]
    assert len(app.window.canvas.strokes) == 2

    candidate_buttons = app.window.ocr_panel.candidate_buttons()
    candidate_buttons[0].click()

    assert app.window.ocr_panel.current_selection_text() == "candidate-2"
    assert app.window.ocr_panel.candidate_texts() == []
    assert app.window.canvas.strokes == []


def test_app_does_not_ink_on_pen_down_transition_frame(tmp_path, monkeypatch, qtbot):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))

    sequence = iter(
        [
            _make_landmarks(index_tip=(0.50, 0.68)),
            _make_landmarks(index_tip=(0.40, 0.22)),
            _make_landmarks(index_tip=(0.41, 0.22)),
            _make_landmarks(index_tip=(0.48, 0.22)),
        ]
    )
    last_landmarks = _make_landmarks(index_tip=(0.50, 0.68))

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

    for _ in range(3):
        app._process_frame()

    assert app.window.canvas.points == []

    qtbot.waitUntil(
        lambda: (app._process_frame() is None or True) and len(app.window.canvas.points) == 1,
        timeout=1000,
    )


def test_app_keeps_single_stroke_across_brief_tracking_dropout(tmp_path, monkeypatch, qtbot):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))

    sequence = iter(
        [
            _make_landmarks(index_tip=(0.50, 0.68)),
            _make_landmarks(index_tip=(0.40, 0.22)),
            _make_landmarks(index_tip=(0.48, 0.22)),
            None,
            _make_landmarks(index_tip=(0.56, 0.22)),
            _make_landmarks(index_tip=(0.64, 0.22)),
            _make_landmarks(index_tip=(0.50, 0.68)),
        ]
    )
    last_landmarks = _make_landmarks(index_tip=(0.50, 0.68))

    def hand_landmark_provider(_frame):
        nonlocal last_landmarks
        try:
            next_value = next(sequence)
        except StopIteration:
            return last_landmarks
        if next_value is not None:
            last_landmarks = next_value
        return next_value

    app = AirWriteApp.for_test(
        camera_source_factory=lambda _settings: ContinuousStubCameraSource(),
        hand_landmark_provider=hand_landmark_provider,
    )
    qtbot.addWidget(app.window)
    app.settings.tracking.gesture_stable_frames = 1
    app.settings.tracking.lost_frame_limit = 2
    app.settings.filter.deadzone = 0.0
    app.settings.filter.strength = 0.0
    app.settings.filter.start_threshold = 0.0
    app._rebuild_interaction_pipeline()

    qtbot.waitUntil(
        lambda: (
            app._process_frame() is None
            or True
        ) and len(app._session_controller.session.strokes) == 1,
        timeout=2000,
    )

    assert len(app._session_controller.session.strokes) == 1
    assert len(app._session_controller.session.strokes[0].points) >= 2


def test_app_splits_stroke_when_dropout_recovers_with_implausible_jump(
    tmp_path, monkeypatch, qtbot
):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))

    sequence = iter(
        [
            _make_landmarks(index_tip=(0.50, 0.68)),
            _make_landmarks(index_tip=(0.40, 0.22)),
            _make_landmarks(index_tip=(0.48, 0.22)),
            None,
            _make_landmarks(index_tip=(0.85, 0.18)),
            _make_landmarks(index_tip=(0.88, 0.18)),
            _make_landmarks(index_tip=(0.50, 0.68)),
        ]
    )
    last_landmarks = _make_landmarks(index_tip=(0.50, 0.68))

    def hand_landmark_provider(_frame):
        nonlocal last_landmarks
        try:
            next_value = next(sequence)
        except StopIteration:
            return last_landmarks
        if next_value is not None:
            last_landmarks = next_value
        return next_value

    app = AirWriteApp.for_test(
        camera_source_factory=lambda _settings: ContinuousStubCameraSource(),
        hand_landmark_provider=hand_landmark_provider,
    )
    qtbot.addWidget(app.window)
    app.settings.tracking.gesture_stable_frames = 1
    app.settings.tracking.lost_frame_limit = 2
    app.settings.filter.deadzone = 0.0
    app.settings.filter.strength = 0.0
    app.settings.filter.start_threshold = 0.0
    app.settings.filter.max_jump_distance = 30.0
    app._rebuild_interaction_pipeline()

    qtbot.waitUntil(
        lambda: (
            app._process_frame() is None
            or True
        ) and len(app._session_controller.session.strokes) == 2,
        timeout=2000,
    )

    assert len(app._session_controller.session.strokes) == 2


def test_skeleton_preview_does_not_clamp_to_a_forced_writing_zone_by_default(
    tmp_path, monkeypatch, qtbot
):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))

    sequence = iter([_make_landmarks(index_tip=(0.45, 0.35))])
    last_landmarks = _make_landmarks(index_tip=(0.45, 0.35))

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
    qtbot.waitUntil(
        lambda: (
            app._process_frame() is None
            or True
        ) and app.window.skeleton_preview.current_overlay() is not None,
        timeout=2000,
    )

    overlay = app.window.skeleton_preview.current_overlay()
    assert overlay is not None
    assert overlay.active_region is None
    assert overlay.raw_tip is not None
    assert overlay.stable_tip is not None


def test_app_maps_left_side_hand_position_into_left_side_canvas_space(
    tmp_path, monkeypatch, qtbot
):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))

    sequence = iter(
        [
            _make_landmarks(index_tip=(0.15, 0.15)),
            _make_landmarks(index_tip=(0.20, 0.15)),
            _make_landmarks(index_tip=(0.25, 0.15)),
        ]
    )
    last_landmarks = _make_landmarks(index_tip=(0.25, 0.15))

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
    app.settings.filter.start_threshold = 0.0
    app._rebuild_interaction_pipeline()
    app.window.resize(1000, 700)
    app.window.show()

    qtbot.waitUntil(
        lambda: (app._process_frame() is None or True) and len(app.window.canvas.points) >= 2,
        timeout=2000,
    )

    first_x, first_y = app.window.canvas.points[0]
    last_x, last_y = app.window.canvas.points[-1]

    assert first_x < 350
    assert first_y < 180
    assert last_x > first_x
    assert abs(last_y - first_y) <= 120


def test_app_stops_inking_as_soon_as_finger_curls_back(tmp_path, monkeypatch, qtbot):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))

    sequence = iter(
        [
            _make_pose(x=0.40, y=0.24, ratio=0.95),
            _make_pose(x=0.48, y=0.24, ratio=0.96),
            _make_pose(x=0.56, y=0.24, ratio=0.78),
            _make_pose(x=0.50, y=0.68, ratio=0.60),
        ]
    )
    last_pose = _make_pose(x=0.50, y=0.68, ratio=0.60)

    def derive_pose(_landmarks):
        nonlocal last_pose
        try:
            last_pose = next(sequence)
        except StopIteration:
            return last_pose
        return last_pose

    monkeypatch.setattr(app_module, "derive_pen_pose", derive_pose)

    app = AirWriteApp.for_test(
        camera_source_factory=lambda _settings: ContinuousStubCameraSource(),
        hand_landmark_provider=lambda _frame: _make_landmarks(index_tip=(0.40, 0.24)),
    )
    qtbot.addWidget(app.window)
    app.settings.tracking.gesture_stable_frames = 1
    app.settings.tracking.landmark_smoothing = 1.0
    app.settings.filter.deadzone = 0.0
    app.settings.filter.strength = 0.0
    app.settings.filter.start_threshold = 0.0
    app._rebuild_interaction_pipeline()

    qtbot.waitUntil(
        lambda: (app._process_frame() is None or True) and len(app.window.canvas.points) == 1,
        timeout=2000,
    )
    assert app._session_controller.active_stroke is not None

    qtbot.waitUntil(
        lambda: (
            app._process_frame() is None
            or True
        ) and len(app.window.canvas.points) == 1
        and app._session_controller.active_stroke is not None,
        timeout=2000,
    )


def test_app_keeps_single_stroke_when_uncertain_frame_recovers_to_drawing(
    tmp_path, monkeypatch, qtbot
):
    monkeypatch.setenv("AIRWRITE_ENV", "test")
    monkeypatch.setenv("AIRWRITE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("AIRWRITE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AIRWRITE_LOG_DIR", str(tmp_path / "logs"))

    sequence = iter(
        [
            _make_pose(x=0.40, y=0.24, ratio=0.95),
            _make_pose(x=0.48, y=0.24, ratio=0.96),
            _make_pose(x=0.56, y=0.24, ratio=0.78),
            _make_pose(x=0.64, y=0.24, ratio=0.95),
            _make_pose(x=0.50, y=0.68, ratio=0.60),
        ]
    )
    last_pose = _make_pose(x=0.50, y=0.68, ratio=0.60)

    def derive_pose(_landmarks):
        nonlocal last_pose
        try:
            last_pose = next(sequence)
        except StopIteration:
            return last_pose
        return last_pose

    monkeypatch.setattr(app_module, "derive_pen_pose", derive_pose)

    app = AirWriteApp.for_test(
        camera_source_factory=lambda _settings: ContinuousStubCameraSource(),
        hand_landmark_provider=lambda _frame: _make_landmarks(index_tip=(0.40, 0.24)),
    )
    qtbot.addWidget(app.window)
    app.settings.tracking.gesture_stable_frames = 1
    app.settings.tracking.landmark_smoothing = 1.0
    app.settings.filter.deadzone = 0.0
    app.settings.filter.strength = 0.0
    app.settings.filter.start_threshold = 0.0
    app._rebuild_interaction_pipeline()

    qtbot.waitUntil(
        lambda: (
            app._process_frame() is None
            or True
        ) and len(app.window.canvas.points) == 2
        and len(app._session_controller.session.strokes) == 0,
        timeout=2000,
    )

    qtbot.waitUntil(
        lambda: (
            app._process_frame() is None
            or True
        ) and len(app._session_controller.session.strokes) == 1,
        timeout=2000,
    )

    assert len(app._session_controller.session.strokes) == 1
    assert len(app._session_controller.session.strokes[0].points) == 2


def _make_landmarks(
    *,
    index_tip: tuple[float, float],
    wrist: tuple[float, float] = (0.50, 0.80),
    middle_mcp: tuple[float, float] = (0.50, 0.60),
) -> HandLandmarks:
    return HandLandmarks(
        index_tip=Point2D(*index_tip),
        thumb_tip=Point2D(0.42, 0.60),
        wrist=Point2D(*wrist),
        middle_mcp=Point2D(*middle_mcp),
        confidence=0.99,
    )


def _make_pose(*, x: float, y: float, ratio: float) -> PenPose:
    return PenPose(
        tip=Point2D(x, y),
        raw_tip=Point2D(x, y),
        source="index_chain",
        extension_ratio=ratio,
        confidence=0.99,
    )
