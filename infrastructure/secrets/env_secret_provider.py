# infrastructure/secrets/env_secret_provider.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class EnvSecretProvider:
    fulltime_id_env: str = "FUNNAVI_FULLTIME_ID"
    password_env: str = "FUNNAVI_PASSWORD"

    def get(self) -> Dict[str, Any]:
        fulltime_id = os.getenv(self.fulltime_id_env)
        password = os.getenv(self.password_env)
        if not fulltime_id or not password:
            raise RuntimeError(
                f"Missing secrets. Set {self.fulltime_id_env} and {self.password_env}"
            )
        return {
            self.fulltime_id_env: fulltime_id,
            self.password_env: password,
        }
