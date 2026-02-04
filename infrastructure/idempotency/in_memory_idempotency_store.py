# infrastructure/idempotency/in_memory_idempotency_store.py
from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Set

from domain.ids import IdempotencyKey


@dataclass
class InMemoryIdempotencyStore:
    _lock: Lock = field(default_factory=Lock, init=False)
    _keys: Set[str] = field(default_factory=set, init=False)

    def register(self, key: IdempotencyKey) -> bool:
        with self._lock:
            if key.value in self._keys:
                return False
            self._keys.add(key.value)
            return True
