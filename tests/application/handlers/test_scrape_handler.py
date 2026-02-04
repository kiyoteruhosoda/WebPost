from __future__ import annotations

from typing import Any, Dict, List

from application.handlers.scrape_handler import ScrapeStepHandler
from application.services.execution_deps import ExecutionDeps
from domain.run import LastResponse, RunContext
from domain.steps.scrape import ScrapeStep


class MockLogger:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def debug(self, event: str, **fields: Any) -> None:
        self.calls.append({"event": event, "level": "debug", **fields})

    def info(self, event: str, **fields: Any) -> None:
        self.calls.append({"event": event, "level": "info", **fields})

    def error(self, event: str, **fields: Any) -> None:
        self.calls.append({"event": event, "level": "error", **fields})

    def warning(self, event: str, **fields: Any) -> None:
        self.calls.append({"event": event, "level": "warning", **fields})

    def bind(self, **fields: Any) -> "MockLogger":
        return self


class MockSecretProvider:
    def get(self) -> Dict[str, Any]:
        return {}


class MockUrlResolver:
    def resolve_url(self, url: str) -> str:
        return url


def test_scrape_step_saves_to_state() -> None:
    logger = MockLogger()
    deps = ExecutionDeps(
        secret_provider=MockSecretProvider(),
        url_resolver=MockUrlResolver(),
        logger=logger,
    )

    html = "<html><body><span class='value'>hello</span></body></html>"
    ctx = RunContext(
        vars={},
        state={},
        last=LastResponse(status=200, url="https://example.com", text=html, headers={}),
    )

    step = ScrapeStep(
        id="scrape1",
        name="scrape1",
        command="css",
        selector=".value",
        save_as="result",
        save_to="state",
        source="last.text",
    )

    handler = ScrapeStepHandler()

    outcome = handler.handle(step, ctx, deps)

    assert outcome.ok is True
    assert ctx.state["result"] == "hello"
    assert ctx.vars == {}
