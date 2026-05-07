from __future__ import annotations

from types import SimpleNamespace

from api import main
from api.main import RunScenarioRequest
from application.handlers.browser_handler import BrowserStepHandler
from domain.steps.browser import BrowserStep
from domain.steps.http import HttpRequestSpec, HttpStep


def _scenario_with_steps(steps: list) -> SimpleNamespace:
    return SimpleNamespace(
        defaults=SimpleNamespace(http=SimpleNamespace(base_url="https://example.com")),
        steps=steps,
    )


def test_build_components_without_browser_step_does_not_create_playwright_client(monkeypatch) -> None:
    created = {"count": 0}

    class DummyBrowserClient:
        def __init__(self, headless: bool = True) -> None:
            created["count"] += 1

    monkeypatch.setattr(main, "PlaywrightBrowserClient", DummyBrowserClient)

    scenario = _scenario_with_steps([
        HttpStep(id="h1", name="h1", request=HttpRequestSpec(method="GET", url="/"))
    ])
    request = RunScenarioRequest(vars={}, secrets={})

    executor, _ctx, _deps, browser_client = main._build_execution_components(
        scenario,
        request,
        main._build_logger("run-1"),
        "run-1",
    )

    assert browser_client is None
    assert created["count"] == 0
    assert all(not isinstance(h, BrowserStepHandler) for h in executor._registry._handlers)


def test_build_components_with_browser_step_registers_browser_handler(monkeypatch) -> None:
    created = {"count": 0}

    class DummyBrowserClient:
        def __init__(self, headless: bool = True) -> None:
            created["count"] += 1

    monkeypatch.setattr(main, "PlaywrightBrowserClient", DummyBrowserClient)

    scenario = _scenario_with_steps([
        BrowserStep(id="b1", name="b1", action="goto", url="/home")
    ])
    request = RunScenarioRequest(vars={}, secrets={})

    executor, _ctx, _deps, browser_client = main._build_execution_components(
        scenario,
        request,
        main._build_logger("run-2"),
        "run-2",
    )

    assert browser_client is not None
    assert created["count"] == 1
    assert any(isinstance(h, BrowserStepHandler) for h in executor._registry._handlers)
