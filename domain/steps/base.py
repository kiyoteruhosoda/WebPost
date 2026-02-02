# domain/steps/base.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class RetryPolicy:
    max: int = 0
    backoff_sec: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class OnErrorRule:
    when_expr: Optional[str]  # None => else
    action: str               # "goto" | "retry" | "abort"
    goto_step_id: Optional[str] = None


@dataclass(frozen=True)
class Step:
    id: str
    name: str
    enabled: bool = field(default=True, kw_only=True)
    retry: RetryPolicy = field(default_factory=RetryPolicy, kw_only=True)
    on_error: List[OnErrorRule] = field(default_factory=list, kw_only=True)