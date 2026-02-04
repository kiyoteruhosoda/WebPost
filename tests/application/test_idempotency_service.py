from __future__ import annotations

from application.exceptions import IdempotencyError
from application.ports.idempotency_store import IdempotencyStorePort
from application.services.idempotency_service import IdempotencyService
from domain.ids import IdempotencyKey


class FakeIdempotencyStore(IdempotencyStorePort):
    def __init__(self) -> None:
        self._keys: set[str] = set()

    def register(self, key: IdempotencyKey) -> bool:
        if key.value in self._keys:
            return False
        self._keys.add(key.value)
        return True


def test_register_or_raise_accepts_new_key() -> None:
    # Arrange
    store = FakeIdempotencyStore()
    service = IdempotencyService(store)

    # Act
    service.register_or_raise(IdempotencyKey("key-1"))

    # Assert
    assert "key-1" in store._keys


def test_register_or_raise_rejects_duplicate_key() -> None:
    # Arrange
    store = FakeIdempotencyStore()
    service = IdempotencyService(store)
    service.register_or_raise(IdempotencyKey("key-1"))

    # Act / Assert
    try:
        service.register_or_raise(IdempotencyKey("key-1"))
    except IdempotencyError as exc:
        assert str(exc) == "Idempotency key already used"
        return
    raise AssertionError("Expected IdempotencyError to be raised")
