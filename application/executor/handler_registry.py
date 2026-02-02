# application/executor/handler_registry.py
from __future__ import annotations

from typing import List

from application.handlers.base import StepHandler
from domain.steps.base import Step


class HandlerRegistry:
    def __init__(self, handlers: List[StepHandler]):
        self._handlers = handlers

    def get_handler(self, step: Step) -> StepHandler:
        for h in self._handlers:
            if h.supports(step):
                return h
        raise RuntimeError(f"No handler found for step: {type(step).__name__} ({step.id})")
