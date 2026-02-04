from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from application.ports.logger import LoggerPort


@dataclass(frozen=True)
class CompositeLogger(LoggerPort):
    loggers: List[LoggerPort]

    def bind(self, **fields: Any) -> "CompositeLogger":
        return CompositeLogger([logger.bind(**fields) for logger in self.loggers])

    def debug(self, event: str, **fields: Any) -> None:
        self._emit("debug", event, fields)

    def info(self, event: str, **fields: Any) -> None:
        self._emit("info", event, fields)

    def error(self, event: str, **fields: Any) -> None:
        self._emit("error", event, fields)

    def _emit(self, level: str, event: str, fields: dict[str, Any]) -> None:
        for logger in self.loggers:
            getattr(logger, level)(event, **fields)
