# infrastructure/logging/console_logger.py
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict

from application.ports.logger import LoggerPort


@dataclass(frozen=True)
class ConsoleLogger(LoggerPort):
    bound: Dict[str, Any] = field(default_factory=dict)

    def bind(self, **fields: Any) -> "ConsoleLogger":
        merged = dict(self.bound)
        merged.update(fields)
        return ConsoleLogger(bound=merged)

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
        print(f"{event} {json.dumps(payload, ensure_ascii=False)}")
