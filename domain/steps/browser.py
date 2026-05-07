from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from domain.steps.base import Step


@dataclass(frozen=True)
class BrowserStep(Step):
    action: str
    url: Optional[str] = None
    selector: Optional[str] = None
    value: Optional[str] = None
    attr: Optional[str] = None
    save_as: Optional[str] = None
    timeout_ms: Optional[int] = None
