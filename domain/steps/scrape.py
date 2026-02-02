# domain/steps/scrape.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from domain.steps.base import Step


@dataclass(frozen=True)
class ScrapeStep(Step):
    command: str               # "hidden_inputs" or "css"
    save_as: str
    selector: Optional[str] = None
    attr: Optional[str] = None
    multiple: bool = False
