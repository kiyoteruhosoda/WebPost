from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from domain.scenario import Scenario
from domain.scenario_input_validator import ScenarioInputValidator


@dataclass(frozen=True)
class ScenarioInputValidatorService:
    validator: ScenarioInputValidator

    def validate(self, scenario: Scenario, provided_vars: Dict[str, Any]) -> None:
        self.validator.validate(scenario.inputs, provided_vars)

    @classmethod
    def default(cls) -> "ScenarioInputValidatorService":
        return cls(validator=ScenarioInputValidator())
