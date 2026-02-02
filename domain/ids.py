# domain/ids.py
from dataclasses import dataclass

@dataclass(frozen=True)
class ScenarioId:
    value: int

@dataclass(frozen=True)
class RunId:
    value: str

@dataclass(frozen=True)
class ScenarioVersion:
    value: int
