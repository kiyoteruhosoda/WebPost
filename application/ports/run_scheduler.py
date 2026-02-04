from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional

from concurrent.futures import Future


class RunSchedulerPort(ABC):
    @abstractmethod
    def submit(self, run_id: str, task: Callable[[], None]) -> Future:
        ...

    @abstractmethod
    def wait(self, run_id: str, timeout_sec: float) -> bool:
        ...

    @abstractmethod
    def get_future(self, run_id: str) -> Optional[Future]:
        ...
