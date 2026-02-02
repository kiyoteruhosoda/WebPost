# application/handlers/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from application.outcome import StepOutcome
from domain.steps.base import Step

if TYPE_CHECKING:
    from domain.run import RunContext
    from application.services.execution_deps import ExecutionDeps


class StepHandler(ABC):
    @abstractmethod
    def supports(self, step: Step) -> bool: ...

    @abstractmethod
    def handle(self, step: Step, ctx: "RunContext", deps: "ExecutionDeps") -> StepOutcome: ...
