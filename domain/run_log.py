from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass(frozen=True)
class RunLogEntry:
    timestamp: datetime
    event: str
    fields: Dict[str, Any]
