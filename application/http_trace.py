# application/http_trace.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

HeaderDict = Dict[str, str]
PairList = List[Tuple[str, str]]

@dataclass(frozen=True)
class CookieSnapshot:
    items: List[Dict[str, Any]]

@dataclass(frozen=True)
class HttpResponseMeta:
    status: int
    url: str
    headers: HeaderDict
    encoding: Optional[str]
    content_type: Optional[str]
    history: List[Dict[str, Any]]
    body_len: int
    body_sha256: str

@dataclass(frozen=True)
class HttpTrace:
    run_id: str
    step_id: str
    method: str
    url: str
    allow_redirects: Optional[bool] = None  # ★デフォルト追加（既存呼び出し互換）
    request_headers: HeaderDict = None  # type: ignore[assignment]
    request_form: PairList = None       # type: ignore[assignment]
    merged_from: Optional[str] = None
    merged_count: int = 0
    collision_keys: List[str] = None    # type: ignore[assignment]
    cookies_before: CookieSnapshot = None  # type: ignore[assignment]
    cookies_after: CookieSnapshot = None   # type: ignore[assignment]
    response: HttpResponseMeta = None       # type: ignore[assignment]
    text_head: str = ""
    html_title: Optional[str] = None
    full_text: str = ""
    raw_bytes: Optional[bytes] = None