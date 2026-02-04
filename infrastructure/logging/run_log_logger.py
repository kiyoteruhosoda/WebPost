from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from application.ports.logger import LoggerPort
from application.ports.run_log_store import RunLogStorePort
from domain.run_log import RunLogEntry


@dataclass(frozen=True)
class RunLogLogger(LoggerPort):
    run_id: str
    log_store: RunLogStorePort
    bound: Dict[str, Any] = field(default_factory=dict)

    def bind(self, **fields: Any) -> "RunLogLogger":
        merged = dict(self.bound)
        merged.update(fields)
        return RunLogLogger(run_id=self.run_id, log_store=self.log_store, bound=merged)

    def debug(self, event: str, **fields: Any) -> None:
        self._emit(event, fields)

    def info(self, event: str, **fields: Any) -> None:
        self._emit(event, fields)

    def error(self, event: str, **fields: Any) -> None:
        self._emit(event, fields)

    def _emit(self, event: str, fields: Dict[str, Any]) -> None:
        payload = dict(self.bound)
        payload.update(fields)
        payload.setdefault("type", event)
        entry = RunLogEntry(
            timestamp=datetime.now(timezone.utc),
            event=event,
            fields=payload,
        )
        self.log_store.append(self.run_id, entry)
