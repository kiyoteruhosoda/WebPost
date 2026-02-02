# infrastructure/http/http_artifact_saver.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Dict

from application.http_trace import HttpTrace
from application.http_trace_enricher import HttpTraceEnricher
from application.services.execution_deps import ExecutionDeps


class HttpArtifactSaver(HttpTraceEnricher):
    """
    1 request  -> 1_
    2 response -> 2_
    3 html     -> 3_

    同一 run_id + body_sha256 は同一フォルダに集約する
    """

    def __init__(self, root: str = "tmp/http"):
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

        # run_id + sha256 -> timestamp
        self._dir_cache: Dict[tuple[str, str], str] = {}
        self._index: int = 0

    def enrich_and_log(self, trace: HttpTrace, deps: ExecutionDeps) -> None:

        # ★ 同一 run_id + sha256 は同一 timestamp を使う
        if trace.run_id not in self._dir_cache:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
            self._dir_cache[trace.run_id] = ts
        else:
            ts = self._dir_cache[trace.run_id]

        base = self._root / f"{ts}_{trace.run_id}"
        base.mkdir(parents=True, exist_ok=True)

        step = trace.step_id

        # ---------- 1. REQUEST ----------
        req_path = base / f"{ts}_{self._index:03}_{step}.req"
        if not req_path.exists():
            with req_path.open("w", encoding="utf-8", errors="ignore") as f:
                f.write(f"{trace.method} {trace.url}\n")
                for k, v in trace.request_headers.items():
                    f.write(f"{k}: {v}\n")
                f.write("\n")
                for k, v in trace.request_form:
                    f.write(f"{k}={v}\n")
        self._index += 1

        # ---------- 2. RESPONSE HEADER ----------
        resp_path = base / f"{ts}_{self._index:03}_{step}.resp"
        if not resp_path.exists():
            with resp_path.open("w", encoding="utf-8", errors="ignore") as f:
                f.write(f"HTTP {trace.response.status}\n")
                for k, v in trace.response.headers.items():
                    f.write(f"{k}: {v}\n")
        self._index += 1

        # ---------- 3. HTML ----------
        html_path = base / f"{ts}_{self._index:03}_{step}.html"
        if not html_path.exists():
            if trace.raw_bytes is not None:
                html_path.write_bytes(trace.raw_bytes)
            else:
                html_path.write_text(
                    trace.full_text or "",
                    encoding="utf-8",
                    errors="ignore",
                )
        self._index += 1

        deps.logger.info(
            "http.artifacts.saved",
            step_id=trace.step_id,
            dir=str(base),
            sha256=trace.response.body_sha256,
        )
