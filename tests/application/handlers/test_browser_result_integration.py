from __future__ import annotations

from dataclasses import dataclass

from application.executor.handler_registry import HandlerRegistry
from application.executor.step_executor import StepExecutor
from application.handlers.browser_handler import BrowserStepHandler
from application.handlers.result_handler import ResultStepHandler
from application.services.execution_deps import ExecutionDeps
from application.services.template_renderer import TemplateRenderer
from domain.run import RunContext
from domain.steps.browser import BrowserStep
from domain.steps.result import ResultStep


class DummyBrowserClient:
    def goto(self, url: str, timeout_ms=None) -> None: return None
    def click(self, selector: str, timeout_ms=None) -> None: return None
    def fill(self, selector: str, value: str, timeout_ms=None) -> None: return None
    def select(self, selector: str, value: str, timeout_ms=None) -> None: return None
    def wait_for_selector(self, selector: str, timeout_ms=None) -> None: return None
    def wait_for_url(self, url: str, timeout_ms=None) -> None: return None
    def text(self, selector: str) -> str: return "Example Domain"
    def attr(self, selector: str, attr: str) -> str: return ""
    def screenshot(self, path=None) -> str: return path or ""
    def close(self) -> None: return None


@dataclass(frozen=True)
class DummySecretProvider:
    def get(self) -> dict: return {}


@dataclass(frozen=True)
class DummyUrlResolver:
    def resolve_url(self, url: str) -> str: return url


@dataclass(frozen=True)
class DummyLogger:
    def info(self, _message: str, **_kwargs) -> None: return None
    def error(self, _message: str, **_kwargs) -> None: return None
    def debug(self, _message: str, **_kwargs) -> None: return None
    def bind(self, **_kwargs): return self


def test_browser_text_can_be_returned_in_result_step() -> None:
    renderer = TemplateRenderer()
    handlers = [BrowserStepHandler(DummyBrowserClient(), renderer), ResultStepHandler(renderer)]
    registry = HandlerRegistry(handlers)
    executor = StepExecutor(registry)

    steps = [
        BrowserStep(id="extract", name="extract", action="text", selector="h1", save_as="title"),
        ResultStep(id="result", name="result", fields={"title": "${state.title}"}),
    ]
    ctx = RunContext(run_id="r1", vars={}, state={}, result={})
    deps = ExecutionDeps(DummySecretProvider(), DummyUrlResolver(), DummyLogger())

    result = executor.execute(steps, ctx, deps)

    assert result.ok is True
    assert ctx.result == {"title": "Example Domain"}
