from __future__ import annotations

from typing import Any

STABLE_TRACKING_DEFAULTS = {
    "min_detection_confidence": 0.65,
    "gesture_stable_frames": 3,
    "lost_frame_limit": 18,
}

STABLE_FILTER_DEFAULTS = {
    "type": "deadzone",
    "strength": 0.70,
    "deadzone": 2.0,
    "start_threshold": 0.0,
    "max_jump_distance": 320.0,
}


def migrate_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    migrated = _deep_copy_payload(payload)
    changed = False

    tracking = migrated.setdefault("tracking", {})
    filter_settings = migrated.setdefault("filter", {})

    for key, value in STABLE_TRACKING_DEFAULTS.items():
        current = tracking.get(key)
        if current is None or current < value:
            tracking[key] = value
            changed = True

    if filter_settings.get("type", "deadzone").strip().lower() != "passthrough":
        if filter_settings.get("type") != "deadzone":
            filter_settings["type"] = "deadzone"
            changed = True

    for key, value in STABLE_FILTER_DEFAULTS.items():
        if key == "type":
            continue
        current = filter_settings.get(key)
        if current is None:
            filter_settings[key] = value
            changed = True
            continue
        if key in {"strength", "max_jump_distance"} and current < value:
            filter_settings[key] = value
            changed = True
        if key in {"deadzone", "start_threshold"} and current > value:
            filter_settings[key] = value
            changed = True

    return migrated, changed


def _deep_copy_payload(payload: dict[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            copied[key] = dict(value)
        else:
            copied[key] = value
    return copied
