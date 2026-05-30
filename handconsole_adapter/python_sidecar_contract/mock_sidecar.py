"""Mock AirInk JSONL sidecar.

This script is only for validating the adapter bridge. It emits normalized hand
tracking frames to stdout as newline-delimited JSON.

Run manually:

    python handconsole_adapter/python_sidecar_contract/mock_sidecar.py
"""

from __future__ import annotations

import json
import math
import sys
import time


def main() -> int:
    frame_id = 0
    start = time.time()
    while True:
        frame_id += 1
        t = time.time() - start
        x = 0.5 + 0.24 * math.sin(t * 1.7)
        y = 0.5 + 0.18 * math.cos(t * 2.3)
        pinch = 0.31 + 0.12 * math.sin(t * 1.2)
        frame = {
            "timestamp_ms": int(time.time() * 1000),
            "frame_id": frame_id,
            "hand_detected": True,
            "raw_tip": {"x": x, "y": y},
            "stable_tip": {"x": x, "y": y},
            "pinch_ratio": pinch,
            "extension_ratio": 0.92,
            "confidence": 0.95,
        }
        print(json.dumps(frame, separators=(",", ":")), flush=True)
        time.sleep(1 / 30)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("mock sidecar stopped", file=sys.stderr)
        raise SystemExit(0)
