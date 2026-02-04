# domain/run.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LastResponse:
    status: int
    url: str
    text: str
    headers: Dict[str, str]


@dataclass
class RunContext:
    run_id: str = ""  # ★追加

    vars: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    last: Optional[LastResponse] = None
    result: Optional[Dict[str, Any]] = None
