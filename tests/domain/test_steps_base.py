# tests/domain/test_steps_base.py
import pytest
from domain.steps.base import RetryPolicy, OnErrorRule, Step


class TestRetryPolicy:
    def test_create_default_retry_policy(self):
        policy = RetryPolicy()
        assert policy.max == 0
        assert policy.backoff_sec == []

    def test_create_retry_policy_with_values(self):
        policy = RetryPolicy(max=3, backoff_sec=[1, 2, 4])
        assert policy.max == 3
        assert policy.backoff_sec == [1, 2, 4]

    def test_retry_policy_frozen(self):
        policy = RetryPolicy(max=3)
        with pytest.raises(Exception):  # FrozenInstanceError
            policy.max = 5


class TestOnErrorRule:
    def test_create_on_error_rule_goto(self):
        rule = OnErrorRule(
            when_expr="status == 500",
            action="goto",
            goto_step_id="error_handler"
        )
        assert rule.when_expr == "status == 500"
        assert rule.action == "goto"
        assert rule.goto_step_id == "error_handler"

    def test_create_on_error_rule_retry(self):
        rule = OnErrorRule(
            when_expr=None,
            action="retry"
        )
        assert rule.when_expr is None
        assert rule.action == "retry"
        assert rule.goto_step_id is None

    def test_create_on_error_rule_abort(self):
        rule = OnErrorRule(
            when_expr="critical_error",
            action="abort"
        )
        assert rule.when_expr == "critical_error"
        assert rule.action == "abort"

    def test_on_error_rule_frozen(self):
        rule = OnErrorRule(when_expr=None, action="retry")
        with pytest.raises(Exception):  # FrozenInstanceError
            rule.action = "abort"


class TestStep:
    def test_create_minimal_step(self):
        step = Step(id="step1", name="Test Step")
        assert step.id == "step1"
        assert step.name == "Test Step"
        assert step.enabled is True
        assert step.retry.max == 0
        assert step.on_error == []

    def test_create_step_disabled(self):
        step = Step(id="step2", name="Disabled Step", enabled=False)
        assert step.id == "step2"
        assert step.enabled is False

    def test_create_step_with_retry(self):
        retry_policy = RetryPolicy(max=3, backoff_sec=[1, 2, 4])
        step = Step(id="step3", name="Retry Step", retry=retry_policy)
        assert step.retry.max == 3
        assert step.retry.backoff_sec == [1, 2, 4]

    def test_create_step_with_on_error_rules(self):
        rules = [
            OnErrorRule(when_expr="status == 404", action="goto", goto_step_id="not_found"),
            OnErrorRule(when_expr=None, action="abort")
        ]
        step = Step(id="step4", name="Error Handling Step", on_error=rules)
        assert len(step.on_error) == 2
        assert step.on_error[0].action == "goto"
        assert step.on_error[1].action == "abort"

    def test_create_step_full_configuration(self):
        retry_policy = RetryPolicy(max=2, backoff_sec=[1, 2])
        rules = [OnErrorRule(when_expr="timeout", action="retry")]
        step = Step(
            id="step5",
            name="Full Step",
            enabled=True,
            retry=retry_policy,
            on_error=rules
        )
        assert step.id == "step5"
        assert step.name == "Full Step"
        assert step.enabled is True
        assert step.retry.max == 2
        assert len(step.on_error) == 1

    def test_step_frozen(self):
        step = Step(id="step6", name="Frozen Step")
        with pytest.raises(Exception):  # FrozenInstanceError
            step.id = "step7"
