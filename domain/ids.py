# domain/ids.py
from dataclasses import dataclass

from domain.exceptions import ValidationError

@dataclass(frozen=True)
class ScenarioId:
    value: int

@dataclass(frozen=True)
class RunId:
    value: str

@dataclass(frozen=True)
class ScenarioVersion:
    value: int


@dataclass(frozen=True)
class IdempotencyKey:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValidationError("Idempotency key must not be empty")
