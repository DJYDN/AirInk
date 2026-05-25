from __future__ import annotations

from time import monotonic


def now() -> float:
    return monotonic()


def elapsed_ms(start_time: float) -> float:
    return (monotonic() - start_time) * 1000.0
