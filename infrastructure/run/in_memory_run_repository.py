from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, Optional

from application.ports.run_repository import RunRepositoryPort
from domain.exceptions import RunStateError
from domain.run_record import RunRecord, RunStatus


class InMemoryRunRepository(RunRepositoryPort):
    def __init__(self) -> None:
        self._runs: Dict[str, RunRecord] = {}
        self._lock = Lock()

    def create(self, record: RunRecord) -> None:
        with self._lock:
            if record.run_id in self._runs:
                raise RunStateError(f"Run already exists: {record.run_id}")
            self._runs[record.run_id] = record

    def get(self, run_id: str) -> Optional[RunRecord]:
        with self._lock:
            return self._runs.get(run_id)

    def transition_status(
        self,
        run_id: str,
        expected: RunStatus,
        new_status: RunStatus,
        result: Optional[dict] = None,
        error: Optional[str] = None,
        error_detail: Optional[dict] = None,
    ) -> RunRecord:
        with self._lock:
            record = self._runs.get(run_id)
            if record is None:
                raise RunStateError(f"Run not found: {run_id}")
            if record.status != expected:
                raise RunStateError(
                    f"Invalid run transition: {run_id} {record.status} -> {new_status}"
                )
            updated = record.with_status(
                status=new_status,
                updated_at=datetime.now(timezone.utc),
                result=result,
                error=error,
                error_detail=error_detail,
            )
            self._runs[run_id] = updated
            return updated

    def update_result(self, run_id: str, result: dict) -> RunRecord:
        with self._lock:
            record = self._runs.get(run_id)
            if record is None:
                raise RunStateError(f"Run not found: {run_id}")
            updated = replace(
                record,
                result=result,
                updated_at=datetime.now(timezone.utc),
            )
            self._runs[run_id] = updated
            return updated

    def update_error(self, run_id: str, error: str, error_detail: Optional[dict] = None) -> RunRecord:
        with self._lock:
            record = self._runs.get(run_id)
            if record is None:
                raise RunStateError(f"Run not found: {run_id}")
            updated = replace(
                record,
                error=error,
                error_detail=error_detail,
                updated_at=datetime.now(timezone.utc),
            )
            self._runs[run_id] = updated
            return updated
