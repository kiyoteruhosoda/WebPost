# application/handlers/assert_handler.py
import re
from application.handlers.base import StepHandler
from application.outcome import StepOutcome
from application.services.template_renderer import TemplateRenderer, RenderSources
from domain.run import RunContext
from domain.steps.assertion import AssertStep

class AssertStepHandler(StepHandler):
    def __init__(self):
        self._renderer = TemplateRenderer()
    
    def supports(self, step) -> bool:
        return isinstance(step, AssertStep)

    def handle(self, step: AssertStep, ctx: RunContext, deps) -> StepOutcome:
        for cond in step.conditions:
            if not self._eval_condition(cond.expr, ctx, deps):
                return StepOutcome(ok=False, error_message=f"assertion failed: {cond.expr}")
        return StepOutcome(ok=True)
    
    def _eval_condition(self, expr: str, ctx: RunContext, deps) -> bool:
        """
        条件式を評価（簡易実装）
        例: "${last.status}==200"
        """
        try:
            src = RenderSources(
                vars=ctx.vars,
                state=ctx.state,
                secrets=deps.secret_provider.get(),
                last=self._last_to_dict(ctx.last),
            )
            
            rendered = self._renderer._render_str_scalar(expr, src)
            
            # 簡易評価: "値==200", "値>=500" など
            if "==" in rendered:
                left, right = rendered.split("==", 1)
                return left.strip() == right.strip()
            elif ">=" in rendered:
                left, right = rendered.split(">=", 1)
                try:
                    return int(left.strip()) >= int(right.strip())
                except ValueError:
                    return False
            elif "<=" in rendered:
                left, right = rendered.split("<=", 1)
                try:
                    return int(left.strip()) <= int(right.strip())
                except ValueError:
                    return False
            elif rendered.startswith("matches(") and rendered.endswith(")"):
                # matches(value, pattern)
                inner = rendered[8:-1]
                parts = inner.split(",", 1)
                if len(parts) == 2:
                    value = parts[0].strip().strip("'").strip('"')
                    pattern = parts[1].strip().strip("'").strip('"')
                    return bool(re.match(pattern, value))
                return False
            
            # それ以外は真偽値として評価
            return bool(rendered and rendered.lower() not in ("false", "0", ""))
            
        except Exception as e:
            deps.logger.warning("assertion.eval_failed", expr=expr, error=str(e))
            return False

    def _last_to_dict(self, last):
        if last is None:
            return {}
        return {
            "status": getattr(last, "status", 0),
            "url": getattr(last, "url", ""),
            "text": getattr(last, "text", ""),
            "headers": getattr(last, "headers", {}),
        }
