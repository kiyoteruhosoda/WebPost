from __future__ import annotations

import pytest

from domain.exceptions import ValidationError
from domain.scenario import ScenarioInputs
from domain.scenario_input_validator import ScenarioInputValidator


def test_scenario_input_validator_accepts_required_inputs() -> None:
    validator = ScenarioInputValidator()
    inputs = ScenarioInputs(required=["facility_id"])

    validator.validate(inputs, {"facility_id": "001"})


def test_scenario_input_validator_rejects_missing_inputs() -> None:
    validator = ScenarioInputValidator()
    inputs = ScenarioInputs(required=["facility_id", "date"])

    with pytest.raises(ValidationError) as exc_info:
        validator.validate(inputs, {"facility_id": "001"})

    assert "Missing required inputs: date" in str(exc_info.value)
