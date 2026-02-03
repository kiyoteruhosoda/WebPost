# domain/scenario.py
"""
Scenario domain model
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from domain.steps.base import Step


@dataclass(frozen=True)
class ScenarioMeta:
    id: int
    name: str
    version: int
    description: str = ""
    enabled: bool = True
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


@dataclass(frozen=True)
class ScenarioInputs:
    required: List[str] = field(default_factory=list)
    optional: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class HttpDefaults:
    base_url: str = ""
    timeout_sec: int = 20
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ScenarioDefaults:
    http: Optional[HttpDefaults] = None


@dataclass(frozen=True)
class Scenario:
    """
    Scenario aggregate root
    """
    meta: ScenarioMeta
    steps: List[Step]
    inputs: ScenarioInputs = field(default_factory=ScenarioInputs)
    defaults: ScenarioDefaults = field(default_factory=ScenarioDefaults)
