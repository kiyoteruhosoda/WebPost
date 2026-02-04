# application/ports/idempotency_store.py
from __future__ import annotations

from typing import Protocol

from domain.ids import IdempotencyKey


class IdempotencyStorePort(Protocol):
    def register(self, key: IdempotencyKey) -> bool:
        ...
