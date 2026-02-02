# application/services/redactor.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

SENSITIVE_KEYS = {"password", "passwd", "pass", "authorization", "cookie", "set-cookie"}


def mask_value(key: str, value: Any) -> Any:
    if key.lower() in SENSITIVE_KEYS and value is not None:
        return "********"
    return value


def mask_pairs(pairs: List[Tuple[str, str]]) -> List[Tuple[str, Any]]:
    return [(k, mask_value(k, v)) for k, v in pairs]


def mask_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: mask_value(k, v) for k, v in d.items()}
