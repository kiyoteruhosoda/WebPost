from __future__ import annotations

from dataclasses import dataclass

from application.handlers.browser_handler import BrowserStepHandler
from application.services.execution_deps import ExecutionDeps
from application.services.template_renderer import TemplateRenderer
from domain.run import RunContext
from domain.steps.browser import BrowserStep


class DummyBrowserClient:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def goto(self, url: str, timeout_ms=None) -> None:
        self.calls.append(("goto", url, timeout_ms))

    def click(self, selector: str, timeout_ms=None) -> None:
        self.calls.append(("click", selector, timeout_ms))

    def fill(self, selector: str, value: str, timeout_ms=None) -> None:
        self.calls.append(("fill", selector, value, timeout_ms))

    def select(self, selector: str, value: str, timeout_ms=None) -> None:
        self.calls.append(("select", selector, value, timeout_ms))

    def wait_for_selector(self, selector: str, timeout_ms=None) -> None:
        self.calls.append(("wait_for_selector", selector, timeout_ms))

    def wait_for_url(self, url: str, timeout_ms=None) -> None:
        self.calls.append(("wait_for_url", url, timeout_ms))
    def wait_for_load_state(self, state: str = "load", timeout_ms=None) -> None:
        self.calls.append(("wait_for_load_state", state, timeout_ms))

    def text(self, selector: str) -> str:
        self.calls.append(("text", selector))
        return "Example Domain"

    def attr(self, selector: str, attr: str) -> str:
        self.calls.append(("attr", selector, attr))
        return "value"

    def screenshot(self, path=None) -> str:
        self.calls.append(("screenshot", path))
        return path or "tmp/browser/screenshot.png"

    def close(self) -> None:
        return None


@dataclass(frozen=True)
class DummySecretProvider:
    def get(self) -> dict:
        return {"USER_ID": "demo"}


@dataclass(frozen=True)
class DummyUrlResolver:
    def resolve_url(self, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        return f"https://base.example{url}"


@dataclass(frozen=True)
class DummyLogger:
    def info(self, _message: str, **_kwargs) -> None: return None
    def error(self, _message: str, **_kwargs) -> None: return None
    def debug(self, _message: str, **_kwargs) -> None: return None
    def bind(self, **_kwargs): return self


def test_browser_handler_executes_goto() -> None:
    browser = DummyBrowserClient()
    handler = BrowserStepHandler(browser, TemplateRenderer())
    step = BrowserStep(id="open", name="open", action="goto", url="https://example.com")
    ctx = RunContext(run_id="r1", vars={}, state={}, result={})
    deps = ExecutionDeps(DummySecretProvider(), DummyUrlResolver(), DummyLogger())

    outcome = handler.handle(step, ctx, deps)

    assert outcome.ok is True
    assert browser.calls[0] == ("goto", "https://example.com", None)


def test_browser_handler_saves_text_to_state() -> None:
    handler = BrowserStepHandler(DummyBrowserClient(), TemplateRenderer())
    step = BrowserStep(id="title", name="title", action="text", selector="h1", save_as="page_title")
    ctx = RunContext(run_id="r1", vars={}, state={}, result={})
    deps = ExecutionDeps(DummySecretProvider(), DummyUrlResolver(), DummyLogger())

    outcome = handler.handle(step, ctx, deps)

    assert outcome.ok is True
    assert ctx.state["page_title"] == "Example Domain"


def test_browser_handler_resolves_relative_url_for_goto() -> None:
    browser = DummyBrowserClient()
    handler = BrowserStepHandler(browser, TemplateRenderer())
    step = BrowserStep(id="open", name="open", action="goto", url="/login")
    ctx = RunContext(run_id="r1", vars={}, state={}, result={})
    deps = ExecutionDeps(DummySecretProvider(), DummyUrlResolver(), DummyLogger())

    outcome = handler.handle(step, ctx, deps)

    assert outcome.ok is True
    assert browser.calls[0] == ("goto", "https://base.example/login", None)


def test_browser_handler_renders_with_last_context() -> None:
    browser = DummyBrowserClient()
    handler = BrowserStepHandler(browser, TemplateRenderer())
    step = BrowserStep(id="open", name="open", action="goto", url="${last.url}")
    ctx = RunContext(run_id="r1", vars={}, state={}, last={"url": "/from-last"}, result={})
    deps = ExecutionDeps(DummySecretProvider(), DummyUrlResolver(), DummyLogger())

    outcome = handler.handle(step, ctx, deps)

    assert outcome.ok is True
    assert browser.calls[0] == ("goto", "https://base.example/from-last", None)
