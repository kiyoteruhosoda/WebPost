from __future__ import annotations

from fastapi import HTTPException

from api import main
from api.main import RunScenarioRequest
from application.executor.step_executor import ExecutionResult


def test_idempotency_key_not_consumed_on_not_found(monkeypatch) -> None:
    # Arrange
    main.IDEMPOTENCY_STORE._keys.clear()

    def fake_execute(self, steps, ctx, deps):
        return ExecutionResult(ok=True)

    monkeypatch.setattr(main.StepExecutor, "execute", fake_execute)
    request = RunScenarioRequest(idempotency_key="key-404", vars={}, secrets={})

    # Act
    try:
        main.run_scenario("missing_scenario", request)
    except HTTPException as exc:
        assert exc.status_code == 404

    # Assert
    assert "key-404" not in main.IDEMPOTENCY_STORE._keys


def test_idempotency_key_consumed_after_validation(monkeypatch) -> None:
    # Arrange
    main.IDEMPOTENCY_STORE._keys.clear()

    def fake_execute(self, steps, ctx, deps):
        return ExecutionResult(ok=True)

    monkeypatch.setattr(main.StepExecutor, "execute", fake_execute)
    request = RunScenarioRequest(idempotency_key="key-ok", vars={}, secrets={})

    # Act
    response = main.run_scenario("simple_test", request)

    # Assert
    assert response.success is True
    assert "key-ok" in main.IDEMPOTENCY_STORE._keys
