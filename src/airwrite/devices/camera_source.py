from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator

from numpy import ndarray


@dataclass(frozen=True)
class CameraFrame:
    data: ndarray
    index: int


class CameraSource(ABC):
    @abstractmethod
    def frames(self) -> Iterator[CameraFrame]:
        """Yield frames from the configured source."""

    def close(self) -> None:
        """Release any backing resources when a real device exists."""
