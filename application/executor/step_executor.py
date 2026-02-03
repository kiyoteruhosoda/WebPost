# application/executor/step_executor.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import time
import uuid

from application.executor.handler_registry import HandlerRegistry
from application.outcome import StepOutcome
from application.services.execution_deps import ExecutionDeps
from domain.run import RunContext
from domain.steps.base import Step


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    failed_step_id: Optional[str] = None
    error_message: Optional[str] = None


class StepExecutor:
    def __init__(self, registry: HandlerRegistry):
        self._registry = registry

    def execute(self, steps: List[Step], ctx: RunContext, deps: ExecutionDeps) -> ExecutionResult:
        # ★run_id を付与（呼び元が指定していれば尊重）
        if not getattr(ctx, "run_id", ""):
            ctx.run_id = uuid.uuid4().hex

        # ★logger に run_id を bind して、以後のログに自動付与
        deps = deps.with_logger(deps.logger.bind(run_id=ctx.run_id))

        for step in steps:
            if getattr(step, "enabled", True) is False:
                continue

            handler = self._registry.get_handler(step)

            deps.logger.info(
                "step.start",
                step_id=step.id,
                step_type=type(step).__name__,
            )
            t0 = time.perf_counter()

            outcome: StepOutcome = handler.handle(step, ctx, deps)

            deps.logger.info(
                "step.end",
                step_id=step.id,
                ok=(outcome is not None and outcome.ok),
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )

            if outcome is None:
                raise RuntimeError(
                    f"Handler returned None: handler={type(handler).__name__}, step={step.id} ({type(step).__name__})"
                )

            if not outcome.ok:
                return ExecutionResult(
                    ok=False,
                    failed_step_id=step.id,
                    error_message=outcome.error_message,
                )

        return ExecutionResult(ok=True)
