from __future__ import annotations

from application.executor.step_executor import ExecutionResult
from application.services.execution_error_builder import ExecutionErrorBuilder
from domain.run import RunContext, LastResponse


def test_build_from_result_includes_step_and_status() -> None:
    # Arrange
    builder = ExecutionErrorBuilder()
    ctx = RunContext(
        vars={},
        state={},
        last=LastResponse(status=500, url="http://example", text="oops", headers={}),
        result={},
    )
    result = ExecutionResult(ok=False, failed_step_id="step-1", error_message="failed")

    # Act
    detail = builder.build_from_result(result, ctx)

    # Assert
    assert detail.code == "step_failed"
    assert detail.message == "failed"
    assert detail.step_id == "step-1"
    assert detail.last_status == 500


def test_build_from_exception_accepts_missing_context() -> None:
    # Arrange
    builder = ExecutionErrorBuilder()

    # Act
    detail = builder.build_from_exception("boom", None)

    # Assert
    assert detail.code == "exception"
    assert detail.message == "boom"
    assert detail.step_id is None
    assert detail.last_status is None
