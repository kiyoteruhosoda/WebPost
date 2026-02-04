from __future__ import annotations

from dataclasses import dataclass

from application.handlers.assert_handler import AssertStepHandler
from application.services.execution_deps import ExecutionDeps
from domain.run import RunContext
from domain.steps.assertion import AssertStep, ConditionSpec


@dataclass(frozen=True)
class DummySecretProvider:
    def get(self) -> dict:
        return {}


@dataclass(frozen=True)
class DummyUrlResolver:
    def resolve_url(self, url: str) -> str:
        return url


@dataclass(frozen=True)
class DummyLogger:
    def info(self, _message: str, **_kwargs) -> None:
        return None

    def error(self, _message: str, **_kwargs) -> None:
        return None

    def debug(self, _message: str, **_kwargs) -> None:
        return None

    def bind(self, **_kwargs) -> "DummyLogger":
        return self


def _deps() -> ExecutionDeps:
    return ExecutionDeps(
        secret_provider=DummySecretProvider(),
        url_resolver=DummyUrlResolver(),
        logger=DummyLogger(),
    )


def test_assert_handler_any_mode_succeeds_when_any_true() -> None:
    # Arrange
    handler = AssertStepHandler()
    step = AssertStep(
        id="assert-any",
        name="assert-any",
        mode="any",
        conditions=[
            ConditionSpec(expr="false"),
            ConditionSpec(expr="true"),
        ],
    )
    ctx = RunContext(vars={}, state={}, last=None, result={})

    # Act
    outcome = handler.handle(step, ctx, _deps())

    # Assert
    assert outcome.ok is True


def test_assert_handler_all_mode_collects_failure_messages() -> None:
    # Arrange
    handler = AssertStepHandler()
    step = AssertStep(
        id="assert-all",
        name="assert-all",
        mode="all",
        fail_fast=False,
        conditions=[
            ConditionSpec(expr="false", message="first failed"),
            ConditionSpec(expr="false", message="second failed"),
        ],
    )
    ctx = RunContext(vars={}, state={}, last=None, result={})

    # Act
    outcome = handler.handle(step, ctx, _deps())

    # Assert
    assert outcome.ok is False
    assert outcome.error_message == "first failed; second failed"


def test_assert_handler_uses_step_message_on_failure() -> None:
    # Arrange
    handler = AssertStepHandler()
    step = AssertStep(
        id="assert-msg",
        name="assert-msg",
        mode="all",
        message="custom failure",
        conditions=[
            ConditionSpec(expr="false", message="ignored"),
        ],
    )
    ctx = RunContext(vars={}, state={}, last=None, result={})

    # Act
    outcome = handler.handle(step, ctx, _deps())

    # Assert
    assert outcome.ok is False
    assert outcome.error_message == "custom failure"
