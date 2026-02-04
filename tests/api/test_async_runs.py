from __future__ import annotations

import json

from api import main
from api.main import RunScenarioRequest
from application.executor.step_executor import ExecutionResult
from domain.run_record import RunStatus


def _reset_run_stores() -> None:
    main.RUN_REPOSITORY._runs.clear()
    main.RUN_LOG_STORE._logs.clear()


def test_async_run_returns_accepted_and_updates_status(monkeypatch) -> None:
    # Arrange
    _reset_run_stores()

    def fake_execute(self, steps, ctx, deps):
        deps.logger.info("custom.event", step_id="fake")
        ctx.result = {"status": "ok"}
        return ExecutionResult(ok=True)

    monkeypatch.setattr(main.StepExecutor, "execute", fake_execute)
    request = RunScenarioRequest(vars={}, secrets={})

    # Act
    response = main.run_scenario("simple_test", request, wait_sec=0)
    payload = json.loads(response.body.decode())
    run_id = payload["run_id"]

    # Assert
    assert response.status_code == 202
    assert main.RUN_SCHEDULER.wait(run_id, timeout_sec=1) is True
    record = main.RUN_REPOSITORY.get(run_id)
    assert record is not None
    assert record.status == RunStatus.SUCCEEDED
    assert record.result == {"status": "ok"}


def test_async_run_wait_returns_success(monkeypatch) -> None:
    # Arrange
    _reset_run_stores()

    def fake_execute(self, steps, ctx, deps):
        ctx.result = {"status": "ok"}
        return ExecutionResult(ok=True)

    monkeypatch.setattr(main.StepExecutor, "execute", fake_execute)
    request = RunScenarioRequest(vars={}, secrets={})

    # Act
    response = main.run_scenario("simple_test", request, wait_sec=1)

    # Assert
    assert response.success is True
    assert response.result == {"status": "ok"}


def test_run_logs_endpoint_returns_entries(monkeypatch) -> None:
    # Arrange
    _reset_run_stores()

    def fake_execute(self, steps, ctx, deps):
        deps.logger.info("custom.event", step_id="fake")
        ctx.result = {"status": "ok"}
        return ExecutionResult(ok=True)

    monkeypatch.setattr(main.StepExecutor, "execute", fake_execute)
    request = RunScenarioRequest(vars={}, secrets={})

    # Act
    response = main.run_scenario("simple_test", request, wait_sec=0)
    run_id = json.loads(response.body.decode())["run_id"]
    main.RUN_SCHEDULER.wait(run_id, timeout_sec=1)
    logs = main.get_run_logs(run_id)

    # Assert
    assert any(entry.event == "custom.event" for entry in logs)
