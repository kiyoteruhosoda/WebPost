# application/handlers/log_handler.py
from __future__ import annotations

from typing import Any, Dict

from application.handlers.base import StepHandler
from application.outcome import StepOutcome
from application.services.execution_deps import ExecutionDeps
from application.services.template_renderer import RenderSources, TemplateRenderer
from domain.run import RunContext
from domain.steps.log import LogStep


class LogStepHandler(StepHandler):
    def __init__(self, renderer: TemplateRenderer):
        self._renderer = renderer

    def supports(self, step) -> bool:
        return isinstance(step, LogStep)

    def handle(self, step: LogStep, ctx: RunContext, deps: ExecutionDeps) -> StepOutcome:
        try:
            src = RenderSources(
                vars=ctx.vars,
                state=ctx.state,
                secrets=deps.secret_provider.get(),
                last=self._last_to_dict(ctx.last),
            )
            message = self._renderer.render_value(step.message, src)
            rendered_fields = self._render_fields(step.fields, src)
            self._emit_log(
                deps=deps,
                level=step.level,
                step_id=step.id,
                message=message,
                fields=rendered_fields,
            )
            return StepOutcome(ok=True)
        except Exception as exc:
            deps.logger.error(
                "log.step_failed",
                step_id=getattr(step, "id", "unknown"),
                error=str(exc),
            )
            return StepOutcome(ok=False, error_message=str(exc))

    def _emit_log(
        self,
        deps: ExecutionDeps,
        level: str,
        step_id: str,
        message: Any,
        fields: Dict[str, Any],
    ) -> None:
        event = "log"
        if level == "debug":
            deps.logger.debug(event, step_id=step_id, message=message, **fields)
            return
        if level == "error":
            deps.logger.error(event, step_id=step_id, message=message, **fields)
            return
        deps.logger.info(event, step_id=step_id, message=message, **fields)

    def _render_fields(self, fields: Dict[str, Any], src: RenderSources) -> Dict[str, Any]:
        rendered: Dict[str, Any] = {}
        for key, value in fields.items():
            rendered[key] = self._renderer.render_value(value, src)
        return rendered

    def _last_to_dict(self, last) -> Dict[str, Any]:
        if last is None:
            return {}
        return {
            "status": getattr(last, "status", 0),
            "url": getattr(last, "url", ""),
            "text": getattr(last, "text", ""),
            "headers": getattr(last, "headers", {}),
        }
