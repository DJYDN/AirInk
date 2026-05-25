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
        "min_detection_confidence": 0.5,
        "pinch_down_threshold": 0.28,
        "pinch_up_threshold": 0.34,
        "stable_frames": 3,
        "lost_frame_limit": 8,
    },
    "filter": {
        "type": "one_euro",
        "strength": 0.5,
    },
}


def default_settings_payload() -> dict[str, object]:
    return deepcopy(DEFAULT_SETTINGS_PAYLOAD)
