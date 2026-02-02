# application/http_trace_emitter.py
from __future__ import annotations

from typing import Iterable

from application.http_trace import HttpTrace
from application.http_trace_enricher import HttpTraceEnricher
from application.services.execution_deps import ExecutionDeps

class HttpTraceEmitter:
    def __init__(self, enrichers: Iterable[HttpTraceEnricher]):
        self._enrichers = list(enrichers)

    def emit(self, trace: HttpTrace, deps: ExecutionDeps) -> None:
        for e in self._enrichers:
            e.enrich_and_log(trace, deps)