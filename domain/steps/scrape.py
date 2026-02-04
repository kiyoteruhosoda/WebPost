# domain/steps/scrape.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from domain.steps.base import Step


@dataclass(frozen=True)
class ScrapeStep(Step):
    command: str               # "hidden_inputs" | "css" | "label_next_td"
    save_as: str
    save_to: str = "vars"
    source: str = "last.text"
    selector: Optional[str] = None
    attr: Optional[str] = None
    multiple: bool = False
    label: Optional[str] = None
