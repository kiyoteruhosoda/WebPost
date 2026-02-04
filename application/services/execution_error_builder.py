# application/services/execution_error_builder.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from application.executor.step_executor import ExecutionResult
from domain.run import RunContext


@dataclass(frozen=True)
class ExecutionErrorDetail:
    code: str
    message: str
    step_id: Optional[str]
    last_status: Optional[int]


class ExecutionErrorBuilder:
    def build_from_result(self, result: ExecutionResult, ctx: RunContext | None) -> ExecutionErrorDetail:
        message = result.error_message or "Step execution failed"
        return ExecutionErrorDetail(
            code="step_failed",
            message=message,
            step_id=result.failed_step_id,
            last_status=getattr(getattr(ctx, "last", None), "status", None),
        )

    def build_from_exception(self, message: str, ctx: RunContext | None) -> ExecutionErrorDetail:
        return ExecutionErrorDetail(
            code="exception",
            message=message,
            step_id=None,
            last_status=getattr(getattr(ctx, "last", None), "status", None),
        )
