# domain/steps/http.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from domain.steps.base import Step


@dataclass(frozen=True)
class HttpRequestSpec:
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    form_list: Optional[List[Tuple[str, str]]] = None  # multi-value対応
    merge_from_vars: Optional[str] = None  # 例: "login_hidden"


@dataclass(frozen=True)
class HttpStep(Step):
    request: HttpRequestSpec
    save_as_last: bool = True
