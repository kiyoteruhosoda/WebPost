from __future__ import annotations

import sys

import pytest

from application.executor.step_executor import ExecutionResult
from scripts import smoke_run


def test_smoke_run_prints_run_id(monkeypatch, capsys) -> None:
    # Arrange
    def fake_execute(self, steps, ctx, deps):
        ctx.run_id = "run-test"
        return ExecutionResult(ok=True)

    monkeypatch.setattr(smoke_run.StepExecutor, "execute", fake_execute)
    monkeypatch.setattr(sys, "argv", ["smoke_run.py", "scenarios/simple_test.yaml"])

    # Act
    with pytest.raises(SystemExit) as excinfo:
        smoke_run.main()

    # Assert
    captured = capsys.readouterr()
    assert "Run ID: run-test" in captured.out
    assert excinfo.value.code == 0
