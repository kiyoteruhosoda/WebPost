# application/handlers/result_handler.py
from __future__ import annotations

from typing import Any, Dict

from application.handlers.base import StepHandler
from application.outcome import StepOutcome
from application.services.execution_deps import ExecutionDeps
from application.services.template_renderer import RenderSources, TemplateRenderer
from domain.run import RunContext
from domain.steps.result import ResultStep


class ResultStepHandler(StepHandler):
    """
    ResultStepを処理し、ctx.result に最終結果を保存する。
    """

    def __init__(self, renderer: TemplateRenderer):
        self._renderer = renderer

    def supports(self, step) -> bool:
        return isinstance(step, ResultStep)

    def handle(self, step: ResultStep, ctx: RunContext, deps: ExecutionDeps) -> StepOutcome:
        try:
            src = RenderSources(
                vars=ctx.vars,
                state=ctx.state,
                secrets=deps.secret_provider.get(),
                last=self._last_to_dict(ctx.last),
            )

            result: Dict[str, Any] = {}
            for key, template in step.fields.items():
                rendered = self._renderer.render_value(template, src)
                result[key] = rendered

            # ctx に result を保存（Run完了時に使用）
            if not hasattr(ctx, 'result'):
                ctx.result = {}
            ctx.result.update(result)

            deps.logger.info(
                "result.saved",
                step_id=step.id,
                result=result,
            )

            return StepOutcome(ok=True)

        except Exception as e:
            deps.logger.error(
                "result.step_failed",
                step_id=getattr(step, "id", "unknown"),
                error=str(e),
            )
            return StepOutcome(ok=False, error_message=str(e))

    def _last_to_dict(self, last) -> Dict[str, Any]:
        if last is None:
            return {}
        return {
            "status": getattr(last, "status", 0),
            "url": getattr(last, "url", ""),
            "text": getattr(last, "text", ""),
            "headers": getattr(last, "headers", {}),
        }
