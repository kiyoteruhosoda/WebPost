# domain/steps/log.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from domain.steps.base import Step


@dataclass(frozen=True)
class LogStep(Step):
    message: str = ""
    level: str = "info"
    fields: Dict[str, Any] = field(default_factory=dict)
