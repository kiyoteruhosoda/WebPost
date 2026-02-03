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

        step_index_by_id = {step.id: idx for idx, step in enumerate(steps)}
        retry_counts: dict[str, int] = {}
        index = 0

        while index < len(steps):
            step = steps[index]
            if getattr(step, "enabled", True) is False:
                index += 1
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

            if outcome.ok:
                retry_counts.pop(step.id, None)
                index += 1
                continue

            selected_rule = self._select_on_error_rule(step, ctx, deps)
            action = selected_rule.action if selected_rule else None

            if action is None:
                action = "retry" if getattr(step, "retry", None) and step.retry.max > 0 else "abort"

            if action == "retry":
                retries = retry_counts.get(step.id, 0)
                if not getattr(step, "retry", None) or retries >= step.retry.max:
                    return ExecutionResult(
                        ok=False,
                        failed_step_id=step.id,
                        error_message=outcome.error_message,
                    )

                backoff = 0
                if step.retry.backoff_sec:
                    backoff_index = min(retries, len(step.retry.backoff_sec) - 1)
                    backoff = max(0, step.retry.backoff_sec[backoff_index])

                if backoff:
                    deps.logger.info(
                        "step.retry.backoff",
                        step_id=step.id,
                        retry_count=retries + 1,
                        backoff_sec=backoff,
                    )
                    time.sleep(backoff)

                retry_counts[step.id] = retries + 1
                deps.logger.info(
                    "step.retry",
                    step_id=step.id,
                    retry_count=retries + 1,
                )
                continue

            retry_counts.pop(step.id, None)

            if action == "goto":
                goto_step_id = selected_rule.goto_step_id if selected_rule else None
                if not goto_step_id:
                    return ExecutionResult(
                        ok=False,
                        failed_step_id=step.id,
                        error_message="goto requested but goto_step_id is missing",
                    )
                if goto_step_id not in step_index_by_id:
                    return ExecutionResult(
                        ok=False,
                        failed_step_id=step.id,
                        error_message=f"goto target not found: {goto_step_id}",
                    )
                deps.logger.info(
                    "step.goto",
                    step_id=step.id,
                    goto_step_id=goto_step_id,
                )
                index = step_index_by_id[goto_step_id]
                continue

            return ExecutionResult(
                ok=False,
                failed_step_id=step.id,
                error_message=outcome.error_message,
            )

        return ExecutionResult(ok=True)

    def _select_on_error_rule(self, step: Step, ctx: RunContext, deps: ExecutionDeps):
        if not getattr(step, "on_error", None):
            return None

        fallback_rule = None
        for rule in step.on_error:
            if rule.when_expr is None:
                if fallback_rule is None:
                    fallback_rule = rule
                continue
            if deps.eval_condition(rule.when_expr, ctx):
                return rule
        return fallback_rule
