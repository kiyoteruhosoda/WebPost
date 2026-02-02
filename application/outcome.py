# application/outcome.py
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class StepOutcome:
    ok: bool
    error_message: Optional[str] = None
    goto_step_id: Optional[str] = None
