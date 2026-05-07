from __future__ import annotations

from pathlib import Path

from application.handlers.base import StepHandler
from application.outcome import StepOutcome
from application.ports.browser_client import BrowserClientPort
from application.services.execution_deps import ExecutionDeps
from application.services.template_renderer import RenderSources, TemplateRenderer
from domain.run import RunContext
from domain.steps.browser import BrowserStep


class BrowserStepHandler(StepHandler):
    def __init__(self, browser_client: BrowserClientPort, renderer: TemplateRenderer) -> None:
        self._browser = browser_client
        self._renderer = renderer

    def supports(self, step) -> bool:
        return isinstance(step, BrowserStep)

    def handle(self, step: BrowserStep, ctx: RunContext, deps: ExecutionDeps) -> StepOutcome:
        try:
            src = RenderSources(
                vars=ctx.vars,
                state=ctx.state,
                secrets=deps.secret_provider.get(),
                last={},
            )
            action = step.action.lower()
            timeout_ms = step.timeout_ms

            if action == "goto":
                self._browser.goto(deps.resolve_url(self._render(step.url, src)), timeout_ms)
            elif action == "click":
                self._browser.click(self._render(step.selector, src), timeout_ms)
            elif action == "fill":
                self._browser.fill(self._render(step.selector, src), self._render(step.value, src), timeout_ms)
            elif action == "select":
                self._browser.select(self._render(step.selector, src), self._render(step.value, src), timeout_ms)
            elif action == "wait_for_selector":
                self._browser.wait_for_selector(self._render(step.selector, src), timeout_ms)
            elif action == "wait_for_url":
                self._browser.wait_for_url(deps.resolve_url(self._render(step.url, src)), timeout_ms)
            elif action == "wait_for_load_state":
                state = self._render(step.value, src) or "load"
                self._browser.wait_for_load_state(state=state, timeout_ms=timeout_ms)
            elif action == "text":
                value = self._browser.text(self._render(step.selector, src))
                if step.save_as:
                    ctx.state[step.save_as] = value
            elif action == "attr":
                value = self._browser.attr(self._render(step.selector, src), self._render(step.attr, src))
                if step.save_as:
                    ctx.state[step.save_as] = value
            elif action == "screenshot":
                path = Path("tmp/browser") / ctx.run_id / f"{step.id}.png"
                saved_path = self._browser.screenshot(str(path))
                if step.save_as:
                    ctx.state[step.save_as] = saved_path
            else:
                return StepOutcome(ok=False, error_message=f"Unsupported browser action: {step.action}")

            return StepOutcome(ok=True)
        except Exception as exc:
            try:
                failure_path = Path("tmp/browser") / ctx.run_id / f"{step.id}_error.png"
                self._browser.screenshot(str(failure_path))
                ctx.state[f"{step.id}_error_screenshot"] = str(failure_path)
            except Exception:
                pass
            return StepOutcome(ok=False, error_message=str(exc))

    def _render(self, value: str | None, src: RenderSources) -> str:
        return self._renderer.render_value(value, src)
