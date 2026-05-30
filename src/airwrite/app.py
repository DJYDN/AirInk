from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
import sys
import threading
import time
from typing import Callable, Protocol
from urllib.request import urlretrieve

import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from airwrite.config.paths import AppPaths
from airwrite.config.settings import AppSettings, CameraSettings, SettingsManager
from airwrite.devices.camera_source import CameraFrame, CameraSource, OpenCVCameraSource
from airwrite.export.export_png import export_widget_to_png
from airwrite.interaction.gesture_state import GestureClassifier, GestureState
from airwrite.interaction.session_controller import SessionController
from airwrite.tracking.hand_tracker import MediaPipeHandLandmarkProvider
from airwrite.tracking.pen_pose import PenPose, PenPoseSmoother, derive_pen_pose
from airwrite.trajectory.filters import DeadzoneFilter, PassthroughFilter
from airwrite.trajectory.mapping import map_image_to_canvas
from airwrite.trajectory.stroke import StrokePoint
from airwrite.ui.camera_preview import PreviewOverlay
from airwrite.ui.main_window import MainWindow
from airwrite.utils.logger import get_logger
from airwrite.utils.timing import elapsed_ms, now

CameraSourceFactory = Callable[[CameraSettings], CameraSource]
HandLandmarkProvider = Callable[[np.ndarray], object | None]


class OcrProvider(Protocol):
    def recognize(self, image: np.ndarray, *, stroke_count: int) -> list[str]:
        ...


class PlaceholderOcrProvider:
    def recognize(self, image: np.ndarray, *, stroke_count: int) -> list[str]:
        ink_density = 0
        if image.size:
            ink_density = int((255 - float(image.mean())) * 10)
        primary = f"session-{stroke_count}-{ink_density}"
        return [primary, f"strokes-{stroke_count}", "retry"]


@dataclass
class AirWriteApp:
    qt_app: QApplication
    window: MainWindow
    paths: AppPaths
    settings_manager: SettingsManager
    owns_qt_app: bool
    camera_source_factory: CameraSourceFactory | None = None
    hand_landmark_provider: HandLandmarkProvider | None = None
    ocr_provider: OcrProvider | None = None
    camera_retry_delay_seconds: float = 1.0
    _active_region: tuple[float, float, float, float] | None = None

    def __post_init__(self) -> None:
        self.logger = get_logger("airwrite.app", self.paths.log_dir)
        self.settings = self.settings_manager.load()
        self.camera_source_factory = self.camera_source_factory or self._default_camera_source_factory
        self.hand_landmark_provider = self.hand_landmark_provider
        self.ocr_provider = self.ocr_provider or PlaceholderOcrProvider()
        self._camera_source: CameraSource | None = None
        self._camera_frame_queue: Queue[CameraFrame] | None = None
        self._camera_reader_thread: threading.Thread | None = None
        self._camera_stop_event: threading.Event | None = None
        self._camera_next_retry_at = 0.0
        self._camera_last_error: str | None = None
        self._camera_session_id = 0
        self._previous_frame_at: float | None = None
        self._stroke_warmup_frames_remaining = 0
        self._tracking_gap_pending = False
        self._pose_smoother: PenPoseSmoother | None = None
        self._rebuild_interaction_pipeline()
        self._loop_timer = QTimer(self.window)
        self._loop_timer.setInterval(16)
        self._loop_timer.timeout.connect(self._process_frame)
        self.window.undo_requested.connect(self.undo_last_stroke)
        self.window.clear_requested.connect(self.clear_canvas)
        self.window.export_requested.connect(lambda: self.export_png())
        self.window.ocr_panel.candidate_selected.connect(self._confirm_ocr_candidate)
        self.window.load_settings(self.settings)
        self.window.canvas.set_pen_style(
            color=self.settings.pen.color,
            width=self.settings.pen.width,
        )
        self.window.settings_panel.settings_changed.connect(self._save_settings_from_ui)
        self.window.status_bar_widget.set_metrics(drawing_active=False)
        self.window.ocr_panel.reset()

    @classmethod
    def create(cls) -> "AirWriteApp":
        return cls._build(test_mode=False)

    @classmethod
    def for_test(
        cls,
        camera_source_factory: CameraSourceFactory | None = None,
        hand_landmark_provider: HandLandmarkProvider | None = None,
        ocr_provider: OcrProvider | None = None,
    ) -> "AirWriteApp":
        return cls._build(
            test_mode=True,
            camera_source_factory=camera_source_factory,
            hand_landmark_provider=hand_landmark_provider,
            ocr_provider=ocr_provider,
        )

    @classmethod
    def _build(
        cls,
        *,
        test_mode: bool,
        camera_source_factory: CameraSourceFactory | None = None,
        hand_landmark_provider: HandLandmarkProvider | None = None,
        ocr_provider: OcrProvider | None = None,
    ) -> "AirWriteApp":
        qt_app = QApplication.instance()
        owns_qt_app = qt_app is None
        if qt_app is None:
            qt_app = QApplication(sys.argv[:1])

        project_root = Path(__file__).resolve().parents[2]
        paths = AppPaths.from_env(project_root)
        settings_manager = SettingsManager(paths)
        window = MainWindow()

        app = cls(
            qt_app=qt_app,
            window=window,
            paths=paths,
            settings_manager=settings_manager,
            owns_qt_app=owns_qt_app,
            camera_source_factory=camera_source_factory,
            hand_landmark_provider=hand_landmark_provider,
            ocr_provider=ocr_provider,
        )
        if not test_mode:
            app.start_realtime_loop()
        return app

    def start_realtime_loop(self) -> None:
        if not self._loop_timer.isActive():
            self._loop_timer.start()

    def stop_realtime_loop(self) -> None:
        self._loop_timer.stop()
        self._reset_camera_source()
        self._close_hand_landmark_provider()

    def process_mock_point(self, x: int, y: int) -> tuple[int, int]:
        point = self.window.canvas.add_point(x, y)
        self.window.status_bar_widget.set_status(f"Drawing point at {point[0]}, {point[1]}")
        self.window.status_bar_widget.set_metrics(drawing_active=True)
        return point

    def clear_canvas(self) -> None:
        self._session_controller.clear()
        self._point_filter.reset()
        self.window.canvas.clear_points()
        self.window.ocr_panel.reset()
        self.window.status_bar_widget.set_status("Canvas cleared")
        self.window.status_bar_widget.set_metrics(drawing_active=False)

    def undo_last_stroke(self):
        removed = self._session_controller.undo_last_stroke()
        if removed is None:
            point = self.window.canvas.undo_last_point()
            if point is None:
                self.window.status_bar_widget.set_status("Nothing to undo")
                self.window.status_bar_widget.set_metrics(drawing_active=False)
                return None

            self.window.status_bar_widget.set_status("Undid last point")
            self.window.status_bar_widget.set_metrics(
                drawing_active=bool(self.window.canvas.points)
            )
            return point

        self._point_filter.reset()
        self._sync_canvas_from_session()
        self.window.status_bar_widget.set_status("Undid last stroke")
        self.window.status_bar_widget.set_metrics(
            drawing_active=False,
        )
        return removed

    def export_png(self, filename: str = "snapshot.png") -> Path:
        export_path = export_widget_to_png(
            self.window.canvas,
            self.paths.data_dir,
            filename,
        )
        self.window.status_bar_widget.set_status(f"Exported PNG to {export_path.name}")
        return export_path

    def run(self) -> int:
        self.window.show()
        self.start_realtime_loop()
        try:
            return self.qt_app.exec()
        finally:
            self._reset_camera_source()
            self._close_hand_landmark_provider()

    def _process_frame(self) -> None:
        frame_started_at = now()
        self._ensure_camera_source()
        if self._camera_frame_queue is None:
            return None

        frame = self._drain_latest_camera_frame()
        if frame is None:
            if (
                self._camera_reader_thread is not None
                and not self._camera_reader_thread.is_alive()
            ):
                status_message = self._camera_last_error or "Camera stream ended"
                self.window.status_bar_widget.set_status(status_message)
                self.window.camera_preview.show_placeholder(status_message)
                self.window.skeleton_preview.show_placeholder(status_message)
                self._reset_camera_source(schedule_retry=True)
            return None

        frame_data = frame.data
        if self.settings.camera.mirror:
            frame_data = np.ascontiguousarray(frame_data[:, ::-1])

        self.window.camera_preview.show_frame(frame_data)
        hand_landmark_provider = self._ensure_hand_landmark_provider()
        landmarks = hand_landmark_provider(frame_data) if hand_landmark_provider else None
        pose = derive_pen_pose(landmarks) if landmarks is not None else None
        if pose is not None and self._pose_smoother is not None:
            pose = self._pose_smoother.update(pose)
        gesture_state = self._gesture_classifier.update(pose)
        timestamp_ms = now() * 1000.0
        had_active_stroke = self._session_controller.active_stroke is not None
        self._session_controller.update_gesture(gesture_state, timestamp_ms=timestamp_ms)
        if not had_active_stroke and self._session_controller.active_stroke is not None:
            self._stroke_warmup_frames_remaining = 1
        if had_active_stroke and self._session_controller.active_stroke is None:
            self._point_filter.reset()
            self._tracking_gap_pending = False
        if pose is None and gesture_state is GestureState.HAND_LOST and self._pose_smoother is not None:
            self._pose_smoother.reset()
        self._maybe_add_filtered_point(
            landmarks=landmarks,
            pose=pose,
            gesture_state=gesture_state,
            frame_width=frame_data.shape[1],
            frame_height=frame_data.shape[0],
            timestamp_ms=timestamp_ms,
        )

        self.window.skeleton_preview.set_overlay(
            PreviewOverlay(
                gesture=gesture_state.value,
                active_region=self._active_region,
                raw_tip=pose.raw_tip if pose is not None else None,
                stable_tip=pose.tip if pose is not None else None,
            )
        )
        skeleton_frame = self._build_skeleton_frame(frame_data, landmarks, pose, gesture_state)
        self.window.skeleton_preview.show_frame(skeleton_frame)

        if self._session_controller.ready_for_ocr(timestamp_ms=timestamp_ms):
            session_image = self._render_session_image()
            candidates = self.ocr_provider.recognize(
                session_image,
                stroke_count=len(self._session_controller.session.strokes),
            )
            self._session_controller.set_candidates(candidates)
            self.window.ocr_panel.set_candidates(candidates)

        self._sync_canvas_from_session()
        self._sync_ocr_panel()
        latency_ms = elapsed_ms(frame_started_at)
        frame_completed_at = now()
        if self._previous_frame_at is None:
            fps = float(self.settings.camera.fps)
        else:
            frame_interval = max(frame_completed_at - self._previous_frame_at, 1e-6)
            fps = 1.0 / frame_interval
        self._previous_frame_at = frame_completed_at

        self.window.status_bar_widget.set_status(
            self._format_status_message(gesture_state=gesture_state, pose=pose)
        )
        self.window.status_bar_widget.set_metrics(
            drawing_active=gesture_state is GestureState.DRAWING,
            fps=fps,
            latency_ms=latency_ms,
            confidence=0.0 if landmarks is None else landmarks.confidence,
        )
        return None

    def _save_settings_from_ui(self, settings: AppSettings) -> None:
        previous_camera_index = self.settings.camera.index
        self.settings = settings
        self.settings_manager.save(settings)
        self.window.canvas.set_pen_style(
            color=self.settings.pen.color,
            width=self.settings.pen.width,
        )
        self._rebuild_interaction_pipeline()
        if settings.camera.index != previous_camera_index:
            self._reset_camera_source()

    def _default_camera_source_factory(self, camera_settings: CameraSettings) -> CameraSource:
        return OpenCVCameraSource(
            camera_index=camera_settings.index,
            width=camera_settings.width,
            height=camera_settings.height,
            fps=camera_settings.fps,
        )

    def _default_hand_landmark_provider(self) -> HandLandmarkProvider:
        model_path = self._ensure_hand_landmarker_model()
        return MediaPipeHandLandmarkProvider(
            model_path=str(model_path),
            min_detection_confidence=self.settings.tracking.min_detection_confidence,
            min_tracking_confidence=self.settings.tracking.min_tracking_confidence,
            landmark_smoothing=self.settings.tracking.landmark_smoothing,
        )

    def _ensure_hand_landmark_provider(self) -> HandLandmarkProvider | None:
        if self.hand_landmark_provider is None:
            try:
                self.hand_landmark_provider = self._default_hand_landmark_provider()
            except Exception as exc:
                self.window.status_bar_widget.set_status(f"Hand tracker unavailable: {exc}")
                return None
        return self.hand_landmark_provider

    def _ensure_camera_source(self) -> None:
        if self._camera_source is not None or self._camera_reader_thread is not None:
            return

        if time.monotonic() < self._camera_next_retry_at:
            return

        self._camera_frame_queue = Queue(maxsize=1)
        self._camera_stop_event = threading.Event()
        self._camera_last_error = None
        self._camera_session_id += 1
        session_id = self._camera_session_id
        camera_settings = self.settings.camera
        frame_queue = self._camera_frame_queue
        stop_event = self._camera_stop_event
        self._camera_reader_thread = threading.Thread(
            target=self._camera_reader_loop,
            args=(session_id, camera_settings, frame_queue, stop_event),
            name="airwrite-camera-reader",
            daemon=True,
        )
        self._camera_reader_thread.start()

    def _reset_camera_source(self, *, schedule_retry: bool = False) -> None:
        if self._camera_stop_event is not None:
            self._camera_stop_event.set()

        if self._camera_source is not None:
            self._camera_source.close()

        if (
            self._camera_reader_thread is not None
            and self._camera_reader_thread.is_alive()
            and self._camera_reader_thread is not threading.current_thread()
        ):
            self._camera_reader_thread.join(timeout=0.2)

        self._camera_source = None
        self._camera_frame_queue = None
        self._camera_reader_thread = None
        self._camera_stop_event = None
        if schedule_retry:
            self._camera_next_retry_at = time.monotonic() + self.camera_retry_delay_seconds

    def _camera_reader_loop(
        self,
        session_id: int,
        camera_settings: CameraSettings,
        frame_queue: Queue[CameraFrame],
        stop_event: threading.Event,
    ) -> None:
        source: CameraSource | None = None
        try:
            source = self.camera_source_factory(camera_settings)
            if self._camera_session_id == session_id:
                self._camera_source = source

            for frame in source.frames():
                if stop_event.is_set():
                    break

                if frame_queue.full():
                    try:
                        frame_queue.get_nowait()
                    except Empty:
                        pass

                frame_queue.put_nowait(frame)
        except Exception as exc:
            if self._camera_session_id == session_id:
                self._camera_last_error = str(exc)
        finally:
            if source is not None:
                source.close()
            if self._camera_session_id == session_id and self._camera_source is source:
                self._camera_source = None

    def _drain_latest_camera_frame(self) -> CameraFrame | None:
        if self._camera_frame_queue is None:
            return None

        latest_frame: CameraFrame | None = None
        while True:
            try:
                latest_frame = self._camera_frame_queue.get_nowait()
            except Empty:
                return latest_frame

    def _rebuild_interaction_pipeline(self) -> None:
        self._gesture_classifier = GestureClassifier(
            stable_frames=self.settings.tracking.gesture_stable_frames,
            fist_ratio_threshold=self.settings.tracking.fist_ratio_threshold,
            extended_ratio_threshold=self.settings.tracking.extended_ratio_threshold,
            hand_loss_grace_frames=self.settings.tracking.lost_frame_limit,
            pinch_down_threshold=self.settings.tracking.pinch_down_threshold,
            pinch_up_threshold=self.settings.tracking.pinch_up_threshold,
            pen_up_stable_frames=max(self.settings.tracking.gesture_stable_frames, 4),
        )
        self._pose_smoother = PenPoseSmoother(alpha=self.settings.tracking.landmark_smoothing)
        self._session_controller = SessionController(
            ocr_idle_timeout_ms=float(self.settings.tracking.session_idle_timeout_ms),
        )
        self._stroke_warmup_frames_remaining = 0
        self._tracking_gap_pending = False
        filter_type = self.settings.filter.type.strip().lower()
        if filter_type == "passthrough":
            self._point_filter = PassthroughFilter()
        else:
            self._point_filter = DeadzoneFilter(
                deadzone=self.settings.filter.deadzone,
                smoothing=self.settings.filter.strength,
                start_threshold=self.settings.filter.start_threshold,
                max_jump_distance=self.settings.filter.max_jump_distance,
            )

    def _maybe_add_filtered_point(
        self,
        *,
        landmarks,
        pose: PenPose | None,
        gesture_state: GestureState,
        frame_width: int,
        frame_height: int,
        timestamp_ms: float,
    ) -> None:
        if gesture_state is not GestureState.DRAWING:
            return
        if pose is None:
            if self._session_controller.active_stroke is not None:
                self._tracking_gap_pending = True
            return

        normalized_x, normalized_y = self._resolve_drawing_position(pose)
        canvas_x, canvas_y = map_image_to_canvas(
            image_x=normalized_x * frame_width,
            image_y=normalized_y * frame_height,
            image_width=frame_width,
            image_height=frame_height,
            canvas_width=max(self.window.canvas.width(), 1),
            canvas_height=max(self.window.canvas.height(), 1),
            active_region=self._active_region,
        )
        raw_point = StrokePoint(
            x=float(canvas_x),
            y=float(canvas_y),
            t=timestamp_ms,
            confidence=pose.confidence,
        )

        if self._tracking_gap_pending:
            active_stroke = self._session_controller.active_stroke
            can_recover = getattr(self._point_filter, "can_recover_to", None)
            if (
                active_stroke is not None
                and active_stroke.points
                and callable(can_recover)
                and not can_recover(raw_point)
            ):
                self._session_controller.split_active_stroke()
                self._point_filter.reset()
            self._tracking_gap_pending = False

        if self._stroke_warmup_frames_remaining > 0:
            prime_method = getattr(self._point_filter, "prime", None)
            if callable(prime_method):
                prime_method(raw_point)
            self._stroke_warmup_frames_remaining -= 1
            return

        filtered_point = self._point_filter.apply(raw_point)
        if filtered_point is None:
            return

        self._session_controller.add_point(
            filtered_point.x,
            filtered_point.y,
            confidence=filtered_point.confidence,
            timestamp_ms=filtered_point.t,
        )

    def _sync_canvas_from_session(self) -> None:
        self.window.canvas.set_strokes(
            self._session_controller.session.strokes,
            self._session_controller.active_stroke,
        )

    def _sync_ocr_panel(self) -> None:
        self.window.ocr_panel.set_session_info(
            phase=self._session_controller.phase.value,
            stroke_count=len(self._session_controller.session.strokes),
        )

    def _confirm_ocr_candidate(self, candidate: str) -> None:
        self._session_controller.confirm_candidate(candidate)
        self.window.ocr_panel.clear_candidates()
        self._point_filter.reset()
        self._sync_canvas_from_session()
        self._sync_ocr_panel()
        self.window.status_bar_widget.set_status(f"Accepted OCR candidate: {candidate}")

    def _resolve_drawing_position(self, pose: PenPose) -> tuple[float, float]:
        return (pose.tip.x, pose.tip.y)

    def _format_status_message(self, *, gesture_state: GestureState, pose: PenPose | None) -> str:
        if pose is None:
            return f"Camera {self.settings.camera.index} live | State: {gesture_state.value} | Pinch: -- | Ext: --"
        pinch_text = "--" if pose.pinch_ratio is None else f"{pose.pinch_ratio:.2f}"
        return (
            f"Camera {self.settings.camera.index} live | State: {gesture_state.value}"
            f" | Pinch: {pinch_text}"
            f" (down<={self.settings.tracking.pinch_down_threshold:.2f}, up>={self.settings.tracking.pinch_up_threshold:.2f})"
            f" | Ext: {pose.extension_ratio:.2f}/{self.settings.tracking.extended_ratio_threshold:.2f}"
        )

    def _build_skeleton_frame(
        self,
        frame_data: np.ndarray,
        landmarks,
        pose: PenPose | None,
        gesture_state: GestureState,
    ) -> np.ndarray:
        import cv2

        skeleton_frame = frame_data.copy()
        height, width = skeleton_frame.shape[:2]
        if self._active_region is not None:
            left, right, top, bottom = self._active_region
            cv2.rectangle(
                skeleton_frame,
                (int(left * width), int(top * height)),
                (int(right * width), int(bottom * height)),
                (255, 0, 255),
                2,
            )

        if landmarks is not None:
            points = landmarks.all_points or (
                landmarks.wrist,
                landmarks.middle_mcp,
                landmarks.thumb_tip,
                landmarks.index_tip,
            )
            for point in points:
                cv2.circle(
                    skeleton_frame,
                    (int(point.x * width), int(point.y * height)),
                    3,
                    (0, 255, 0),
                    -1,
                )

            cv2.line(
                skeleton_frame,
                (int(landmarks.thumb_tip.x * width), int(landmarks.thumb_tip.y * height)),
                (int(landmarks.index_tip.x * width), int(landmarks.index_tip.y * height)),
                (255, 0, 255),
                2,
            )
            cv2.circle(
                skeleton_frame,
                (int(landmarks.thumb_tip.x * width), int(landmarks.thumb_tip.y * height)),
                5,
                (255, 0, 255),
                -1,
            )
            cv2.circle(
                skeleton_frame,
                (int(landmarks.index_tip.x * width), int(landmarks.index_tip.y * height)),
                5,
                (0, 255, 255),
                -1,
            )

            if landmarks.all_points:
                connections = (
                    (0, 1), (1, 2), (2, 3), (3, 4),
                    (0, 5), (5, 6), (6, 7), (7, 8),
                    (5, 9), (9, 10), (10, 11), (11, 12),
                    (9, 13), (13, 14), (14, 15), (15, 16),
                    (13, 17), (17, 18), (18, 19), (19, 20),
                    (0, 17),
                )
                for start_index, end_index in connections:
                    if start_index >= len(landmarks.all_points) or end_index >= len(landmarks.all_points):
                        continue
                    start = landmarks.all_points[start_index]
                    end = landmarks.all_points[end_index]
                    cv2.line(
                        skeleton_frame,
                        (int(start.x * width), int(start.y * height)),
                        (int(end.x * width), int(end.y * height)),
                        (255, 200, 0),
                        1,
                    )

        if pose is not None:
            cv2.circle(
                skeleton_frame,
                (int(pose.raw_tip.x * width), int(pose.raw_tip.y * height)),
                5,
                (0, 0, 255),
                -1,
            )
            cv2.circle(
                skeleton_frame,
                (int(pose.tip.x * width), int(pose.tip.y * height)),
                5,
                (255, 255, 255),
                2,
            )

        cv2.putText(
            skeleton_frame,
            f"Gesture: {gesture_state.value}",
            (12, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
        if pose is not None:
            pinch_text = "--" if pose.pinch_ratio is None else f"{pose.pinch_ratio:.2f}"
            cv2.putText(
                skeleton_frame,
                (
                    f"Pinch {pinch_text} | Down<= {self.settings.tracking.pinch_down_threshold:.2f}"
                    f" | Up>= {self.settings.tracking.pinch_up_threshold:.2f}"
                ),
                (12, 52),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                skeleton_frame,
                f"Ext {pose.extension_ratio:.2f} | Up>= {self.settings.tracking.extended_ratio_threshold:.2f}",
                (12, 76),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
        return skeleton_frame

    def _render_session_image(self) -> np.ndarray:
        import cv2

        session_image = np.full((256, 256, 3), 255, dtype=np.uint8)
        for stroke in self._session_controller.session.strokes:
            if not stroke.points:
                continue

            points = np.array(
                [[int(point.x), int(point.y)] for point in stroke.points],
                dtype=np.int32,
            )
            if len(points) == 1:
                cv2.circle(session_image, tuple(points[0]), 2, (0, 0, 0), -1)
            else:
                cv2.polylines(session_image, [points], False, (0, 0, 0), 2)
        return session_image

    def _close_hand_landmark_provider(self) -> None:
        close_method = getattr(self.hand_landmark_provider, "close", None)
        if callable(close_method):
            close_method()
        self.hand_landmark_provider = None

    def _ensure_hand_landmarker_model(self) -> Path:
        model_dir = self.paths.root_dir / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / "hand_landmarker.task"
        if not model_path.exists():
            urlretrieve(
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
                model_path,
            )
        return model_path
