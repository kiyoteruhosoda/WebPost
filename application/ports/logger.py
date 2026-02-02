# application/ports/logger.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class LoggerPort(ABC):
    @abstractmethod
    def debug(self, event: str, **fields: Any) -> None:
        ...

    @abstractmethod
    def info(self, event: str, **fields: Any) -> None:
        ...

    @abstractmethod
    def error(self, event: str, **fields: Any) -> None:
        ...

    @abstractmethod
    def bind(self, **fields: Any) -> "LoggerPort":
        """
        Return a logger that will attach given fields to every log event.
        """
        ...
