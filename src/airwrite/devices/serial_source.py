from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class SerialSource(ABC):
    @abstractmethod
    def read(self) -> bytes | None:
        """Read the next payload from the source, if one is available."""

    def close(self) -> None:
        """Release any backing resources when a real device exists."""


@dataclass
class HardwareSerialSource(SerialSource):
    port: str
    baudrate: int = 115200
    timeout_seconds: float = 0.1

    def read(self) -> bytes | None:
        raise RuntimeError("Real serial hardware integration is not implemented yet.")
