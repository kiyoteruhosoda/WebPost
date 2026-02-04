from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from domain.exceptions import ValidationError
from domain.scenario import ScenarioInputs


@dataclass(frozen=True)
class ScenarioInputValidator:
    def validate(self, inputs: ScenarioInputs, provided_vars: Dict[str, Any]) -> None:
        missing = self._find_missing_inputs(inputs.required, provided_vars)
        if missing:
            missing_text = ", ".join(missing)
            raise ValidationError(f"Missing required inputs: {missing_text}")

    def _find_missing_inputs(self, required: List[str], provided_vars: Dict[str, Any]) -> List[str]:
        missing: List[str] = []
        for key in required:
            if key not in provided_vars or provided_vars[key] is None:
                missing.append(key)
        return missing
