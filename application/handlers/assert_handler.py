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
        for cond in step.conditions:
            if not deps.eval_condition(cond.expr, ctx):
                return StepOutcome(ok=False, error_message=f"assertion failed: {cond.expr}")
        return StepOutcome(ok=True)
