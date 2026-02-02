# application/http_trace_enricher.py
from __future__ import annotations

from abc import ABC, abstractmethod

from application.http_trace import HttpTrace
from application.services.execution_deps import ExecutionDeps


class HttpTraceEnricher(ABC):
    @abstractmethod
    def enrich_and_log(self, trace: HttpTrace, deps: ExecutionDeps) -> None:
        ...