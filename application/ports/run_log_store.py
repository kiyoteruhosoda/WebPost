from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from domain.run_log import RunLogEntry


class RunLogStorePort(ABC):
    @abstractmethod
    def append(self, run_id: str, entry: RunLogEntry) -> None:
        ...

    @abstractmethod
    def list(self, run_id: str) -> List[RunLogEntry]:
        ...
