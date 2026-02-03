# domain/steps/assertion.py
from dataclasses import dataclass
from typing import List
from domain.steps.base import Step

@dataclass(frozen=True)
class ConditionSpec:
    expr: str

@dataclass
class AssertStep(Step):
    conditions: List[ConditionSpec] = None
