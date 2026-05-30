from __future__ import annotations

from copy import deepcopy

DEFAULT_SETTINGS_PAYLOAD = {
    "camera": {
        "index": 0,
        "width": 1280,
        "height": 720,
        "fps": 30,
        "mirror": True,
    },
    "canvas": {
        "width": 1280,
        "height": 720,
        "background_color": "#FFFFFF",
    },
    "pen": {
        "color": "#000000",
        "width": 4,
        "opacity": 1.0,
    },
    "tracking": {
        "min_detection_confidence": 0.7,
        "min_tracking_confidence": 0.75,
        "landmark_smoothing": 0.55,
        "pinch_down_threshold": 0.28,
        "pinch_up_threshold": 0.34,
        "stable_frames": 3,
        "lost_frame_limit": 10,
        "gesture_stable_frames": 1,
        "fist_ratio_threshold": 0.65,
        "extended_ratio_threshold": 0.88,
        "session_idle_timeout_ms": 1500,
    },
    "filter": {
        "type": "deadzone",
        "strength": 0.5,
        "deadzone": 4.0,
        "start_threshold": 4.0,
        "max_jump_distance": 180.0,
    },
}


def default_settings_payload() -> dict[str, object]:
    return deepcopy(DEFAULT_SETTINGS_PAYLOAD)
