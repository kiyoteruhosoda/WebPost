from __future__ import annotations

from api import main
from api.main import RunScenarioRequest
from application.executor.step_executor import ExecutionResult
from domain.scenario import Scenario, ScenarioDefaults, ScenarioMeta, HttpDefaults


class FakeLogger:
    def __init__(self, bound: dict[str, object] | None = None, events: list[dict[str, object]] | None = None) -> None:
        self.bound = bound or {}
        self.events = [] if events is None else events

    def bind(self, **fields: object) -> "FakeLogger":
        merged = dict(self.bound)
        merged.update(fields)
        return FakeLogger(bound=merged, events=self.events)

    def info(self, event: str, **fields: object) -> None:
        payload = dict(self.bound)
        payload.update(fields)
        payload["type"] = event
        self.events.append(payload)

    def debug(self, event: str, **fields: object) -> None:
        self.info(event, **fields)

    def error(self, event: str, **fields: object) -> None:
        self.info(event, **fields)


def test_run_start_includes_run_id(monkeypatch) -> None:
    # Arrange
    captured = []

    def fake_logger() -> FakeLogger:
        return FakeLogger(events=captured)

    def fake_execute(self, steps, ctx, deps):
        return ExecutionResult(ok=True)

    scenario = Scenario(
        meta=ScenarioMeta(id=1, name="test", version=1),
        steps=[],
        defaults=ScenarioDefaults(http=HttpDefaults(base_url="https://example.test")),
    )

    monkeypatch.setattr(main.ScenarioFileFinder, "find_by_id", lambda self, _: main.Path("dummy"))
    monkeypatch.setattr(
        main.ScenarioLoaderRegistry,
        "get_loader",
        lambda self, _: type("FakeLoader", (), {"load_from_file": lambda self, __: scenario})(),
    )
    monkeypatch.setattr(main, "ConsoleLogger", fake_logger)
    monkeypatch.setattr(main.StepExecutor, "execute", fake_execute)
    request = RunScenarioRequest(vars={}, secrets={})

    # Act
    response = main.run_scenario("simple_test", request)

    # Assert
    run_start_events = [event for event in captured if event.get("type") == "run.start"]
    assert len(run_start_events) == 1
    assert run_start_events[0].get("scenario_id") == "simple_test"
    assert run_start_events[0].get("run_id")
    assert response.success is True
