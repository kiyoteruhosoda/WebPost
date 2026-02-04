from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from domain.run_record import RunRecord, RunStatus


class RunRepositoryPort(ABC):
    @abstractmethod
    def create(self, record: RunRecord) -> None:
        ...

    @abstractmethod
    def get(self, run_id: str) -> Optional[RunRecord]:
        ...

    @abstractmethod
    def transition_status(
        self,
        run_id: str,
        expected: RunStatus,
        new_status: RunStatus,
        result: Optional[dict] = None,
        error: Optional[str] = None,
        error_detail: Optional[dict] = None,
    ) -> RunRecord:
        ...

    @abstractmethod
    def update_result(self, run_id: str, result: dict) -> RunRecord:
        ...

    @abstractmethod
    def update_error(self, run_id: str, error: str, error_detail: Optional[dict] = None) -> RunRecord:
        ...
