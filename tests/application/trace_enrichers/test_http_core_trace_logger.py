from __future__ import annotations

from typing import Any, Dict, List

from application.http_trace import CookieSnapshot, HttpResponseMeta, HttpTrace
from application.services.execution_deps import ExecutionDeps
from application.trace_enrichers.core import HttpCoreTraceLogger


class MockLogger:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def debug(self, event: str, **fields: Any) -> None:
        self.calls.append({"event": event, "level": "debug", **fields})

    def info(self, event: str, **fields: Any) -> None:
        self.calls.append({"event": event, "level": "info", **fields})

    def error(self, event: str, **fields: Any) -> None:
        self.calls.append({"event": event, "level": "error", **fields})

    def bind(self, **fields: Any) -> "MockLogger":
        return self


class MockSecretProvider:
    def get(self) -> Dict[str, Any]:
        return {}


class MockUrlResolver:
    def resolve_url(self, url: str) -> str:
        return url


def test_http_core_trace_logger_emits_request_and_response() -> None:
    logger = MockLogger()
    deps = ExecutionDeps(
        secret_provider=MockSecretProvider(),
        url_resolver=MockUrlResolver(),
        logger=logger,
    )
    trace = HttpTrace(
        run_id="run1",
        step_id="step1",
        method="GET",
        url="https://example.com",
        allow_redirects=True,
        request_headers={"Authorization": "secret"},
        request_form=[("a", "b")],
        merged_from=None,
        merged_count=0,
        collision_keys=[],
        cookies_before=CookieSnapshot(items=[]),
        cookies_after=CookieSnapshot(items=[]),
        response=HttpResponseMeta(
            status=200,
            url="https://example.com",
            headers={"Set-Cookie": "x"},
            encoding="utf-8",
            content_type="text/html",
            history=[],
            body_len=10,
            body_sha256="hash",
        ),
        text_head="head",
        html_title=None,
    )

    HttpCoreTraceLogger().enrich_and_log(trace, deps)

    events = [call["event"] for call in logger.calls]
    assert "http.request" in events
    assert "http.response" in events
