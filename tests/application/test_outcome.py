# tests/application/test_outcome.py
import pytest
from application.outcome import StepOutcome


class TestStepOutcome:
    def test_create_success_outcome(self):
        outcome = StepOutcome(ok=True)
        assert outcome.ok is True
        assert outcome.error_message is None
        assert outcome.goto_step_id is None

    def test_create_failure_outcome_with_error(self):
        outcome = StepOutcome(ok=False, error_message="Connection failed")
        assert outcome.ok is False
        assert outcome.error_message == "Connection failed"
        assert outcome.goto_step_id is None

    def test_create_outcome_with_goto(self):
        outcome = StepOutcome(ok=True, goto_step_id="next_step")
        assert outcome.ok is True
        assert outcome.goto_step_id == "next_step"

    def test_create_failure_with_goto(self):
        outcome = StepOutcome(
            ok=False,
            error_message="Validation failed",
            goto_step_id="error_handler"
        )
        assert outcome.ok is False
        assert outcome.error_message == "Validation failed"
        assert outcome.goto_step_id == "error_handler"

    def test_outcome_frozen(self):
        outcome = StepOutcome(ok=True)
        with pytest.raises(Exception):  # FrozenInstanceError
            outcome.ok = False
