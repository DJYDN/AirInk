from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from airwrite.devices.serial_source import SerialSource


@dataclass
class MockSerialSource(SerialSource):
    messages: list[bytes] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._messages = deque(self.messages)

    def read(self) -> bytes | None:
        if not self._messages:
            return None

        return self._messages.popleft()
