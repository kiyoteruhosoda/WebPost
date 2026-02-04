from __future__ import annotations

from typing import Any, Dict, List

from application.handlers.log_handler import LogStepHandler
from application.services.execution_deps import ExecutionDeps
from application.services.template_renderer import TemplateRenderer
from domain.run import RunContext
from domain.steps.log import LogStep


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
        return {"token": "secret"}


class MockUrlResolver:
    def resolve_url(self, url: str) -> str:
        return url


def test_log_step_handler_renders_and_logs() -> None:
    logger = MockLogger()
    deps = ExecutionDeps(
        secret_provider=MockSecretProvider(),
        url_resolver=MockUrlResolver(),
        logger=logger,
    )
    ctx = RunContext(vars={"foo": "123"}, state={})
    renderer = TemplateRenderer()
    handler = LogStepHandler(renderer)

    step = LogStep(
        id="log1",
        name="log1",
        message="hello ${vars.foo}",
        level="info",
        fields={"value": "${vars.foo}"},
    )

    outcome = handler.handle(step, ctx, deps)

    assert outcome.ok is True
    assert logger.calls
    call = logger.calls[0]
    assert call["event"] == "log"
    assert call["level"] == "info"
    assert call["message"] == "hello 123"
    assert call["value"] == "123"


def test_log_step_handler_rejects_secret_template() -> None:
    logger = MockLogger()
    deps = ExecutionDeps(
        secret_provider=MockSecretProvider(),
        url_resolver=MockUrlResolver(),
        logger=logger,
    )
    ctx = RunContext(vars={"foo": "123"}, state={})
    renderer = TemplateRenderer()
    handler = LogStepHandler(renderer)

    step = LogStep(
        id="log1",
        name="log1",
        message="token ${secrets.token}",
        level="info",
        fields={},
    )

    outcome = handler.handle(step, ctx, deps)

    assert outcome.ok is False
    assert any(call["event"] == "log.step_failed" for call in logger.calls)
