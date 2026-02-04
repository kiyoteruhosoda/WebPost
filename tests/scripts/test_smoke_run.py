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


def test_smoke_run_start_requests_async_run(monkeypatch, capsys) -> None:
    # Arrange
    captured = {}

    class DummyResponse:
        status_code = 202

        def json(self):
            return {"run_id": "run-123", "status": "queued"}

    def fake_post(url, json, params, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["params"] = params
        captured["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr(smoke_run.requests, "post", fake_post)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "smoke_run.py",
            "start",
            "--scenario-id",
            "simple_test",
            "--api-base-url",
            "http://localhost:8000",
        ],
    )

    # Act
    with pytest.raises(SystemExit) as excinfo:
        smoke_run.main()

    # Assert
    assert captured["url"] == "http://localhost:8000/scenarios/simple_test/runs"
    assert captured["params"] == {"wait_sec": 0}
    assert captured["timeout"] == smoke_run.DEFAULT_API_TIMEOUT_SEC
    assert excinfo.value.code == 0
