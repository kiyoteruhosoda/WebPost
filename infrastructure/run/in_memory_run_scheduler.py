from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
from typing import Callable, Dict, Optional

from application.ports.run_scheduler import RunSchedulerPort


class InMemoryRunScheduler(RunSchedulerPort):
    def __init__(self, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = Lock()
        self._futures: Dict[str, Future] = {}

    def submit(self, run_id: str, task: Callable[[], None]) -> Future:
        with self._lock:
            future = self._executor.submit(task)
            self._futures[run_id] = future
            return future

    def wait(self, run_id: str, timeout_sec: float) -> bool:
        future = self.get_future(run_id)
        if future is None:
            return False
        try:
            future.result(timeout=timeout_sec)
        except Exception:
            return future.done()
        return True

    def get_future(self, run_id: str) -> Optional[Future]:
        with self._lock:
            return self._futures.get(run_id)
