# domain/steps/assertion.py
from dataclasses import dataclass
from typing import List, Optional

from domain.steps.base import Step

@dataclass(frozen=True)
class ConditionSpec:
    expr: str
    message: Optional[str] = None

@dataclass(frozen=True)
class AssertStep(Step):
    conditions: List[ConditionSpec] = None
    mode: str = "all"
    fail_fast: bool = True
    message: Optional[str] = None
