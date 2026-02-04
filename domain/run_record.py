from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    scenario_id: str
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    error_detail: Optional[Dict[str, Any]]

    def with_status(
        self,
        status: RunStatus,
        updated_at: datetime,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        error_detail: Optional[Dict[str, Any]] = None,
    ) -> "RunRecord":
        return RunRecord(
            run_id=self.run_id,
            scenario_id=self.scenario_id,
            status=status,
            created_at=self.created_at,
            updated_at=updated_at,
            result=result if result is not None else self.result,
            error=error if error is not None else self.error,
            error_detail=error_detail if error_detail is not None else self.error_detail,
        )
