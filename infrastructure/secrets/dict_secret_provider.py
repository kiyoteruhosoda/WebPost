# infrastructure/secrets/dict_secret_provider.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class DictSecretProvider:
    secrets: Dict[str, Any]

    def get(self) -> Dict[str, Any]:
        return dict(self.secrets)
