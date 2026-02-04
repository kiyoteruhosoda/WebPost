# application/handlers/assert_handler.py
import re
from application.handlers.base import StepHandler
from application.outcome import StepOutcome
from domain.run import RunContext
from domain.steps.assertion import AssertStep

class AssertStepHandler(StepHandler):
    def supports(self, step) -> bool:
        return isinstance(step, AssertStep)

    def handle(self, step: AssertStep, ctx: RunContext, deps) -> StepOutcome:
        mode = (step.mode or "all").lower()
        if mode not in {"all", "any"}:
            return StepOutcome(ok=False, error_message=f"unsupported assert mode: {step.mode}")

        failures = []
        results = []

        for cond in step.conditions:
            ok = deps.eval_condition(cond.expr, ctx)
            results.append(ok)
            if not ok:
                failures.append(cond.message or f"assertion failed: {cond.expr}")
                if mode == "all" and step.fail_fast:
                    return StepOutcome(ok=False, error_message=self._build_message(step, failures))
            elif mode == "any" and step.fail_fast:
                return StepOutcome(ok=True)

        if mode == "all":
            if all(results):
                return StepOutcome(ok=True)
            return StepOutcome(ok=False, error_message=self._build_message(step, failures))

        if any(results):
            return StepOutcome(ok=True)
        return StepOutcome(ok=False, error_message=self._build_message(step, failures))

    def _build_message(self, step: AssertStep, failures: list[str]) -> str:
        if step.message:
            return step.message
        if failures:
            return "; ".join(failures)
        return "assertion failed"
