from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol


class SecretTemplateError(Exception):
    pass


class SecretTemplatePolicy(Protocol):
    def assert_safe(self, value: Any) -> None:
        ...


@dataclass(frozen=True)
class BlockSecretTemplatePolicy:
    forbidden_token: str = "${secrets"

    def assert_safe(self, value: Any) -> None:
        if self._contains_secret_template(value):
            raise SecretTemplateError("Secret template usage is not allowed in log steps")

    def _contains_secret_template(self, value: Any) -> bool:
        if isinstance(value, str):
            return self.forbidden_token in value
        if isinstance(value, Mapping):
            return any(self._contains_secret_template(v) for v in value.values())
        if isinstance(value, Iterable):
            return any(self._contains_secret_template(v) for v in value)
        return False
