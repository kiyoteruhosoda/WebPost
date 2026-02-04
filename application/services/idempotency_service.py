# application/services/idempotency_service.py
from __future__ import annotations

from dataclasses import dataclass

from application.exceptions import IdempotencyError
from application.ports.idempotency_store import IdempotencyStorePort
from domain.ids import IdempotencyKey


@dataclass(frozen=True)
class IdempotencyService:
    store: IdempotencyStorePort

    def register_or_raise(self, key: IdempotencyKey) -> None:
        if not self.store.register(key):
            raise IdempotencyError("Idempotency key already used")
