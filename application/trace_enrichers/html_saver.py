# application/trace_enrichers/html_saver.py
from __future__ import annotations

from pathlib import Path
from application.http_trace import HttpTrace
from application.http_trace_enricher import HttpTraceEnricher
from application.services.execution_deps import ExecutionDeps

class HtmlSaver(HttpTraceEnricher):
    def __init__(self, out_dir: str = "tmp/http"):
        self._dir = Path(out_dir)

    def enrich_and_log(self, trace: HttpTrace, deps: ExecutionDeps) -> None:
        out_dir = self._dir / trace.run_id
        out_dir.mkdir(parents=True, exist_ok=True)

        name = f"{trace.step_id}_{trace.response.status}_{trace.response.body_sha256[:8]}.html"
        path = out_dir / name

        if trace.raw_bytes is not None:
            path.write_bytes(trace.raw_bytes)  # ★正解
        else:
            # フォールバック
            path.write_text(trace.full_text or "", encoding="utf-8", errors="ignore")

        deps.logger.info("http.saved_html", step_id=trace.step_id, path=str(path))
        
