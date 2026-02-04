from __future__ import annotations

from threading import Lock
from typing import Dict, List

from application.ports.run_log_store import RunLogStorePort
from domain.run_log import RunLogEntry


class InMemoryRunLogStore(RunLogStorePort):
    def __init__(self) -> None:
        self._logs: Dict[str, List[RunLogEntry]] = {}
        self._lock = Lock()

    def append(self, run_id: str, entry: RunLogEntry) -> None:
        with self._lock:
            self._logs.setdefault(run_id, []).append(entry)

    def list(self, run_id: str) -> List[RunLogEntry]:
        with self._lock:
            return list(self._logs.get(run_id, []))
