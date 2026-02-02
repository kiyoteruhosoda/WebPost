# application/ports/http_client.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass(frozen=True)
class HttpHistoryItem:
    status: int
    url: str
    location: Optional[str]
    set_cookie: Optional[str]


@dataclass(frozen=True)
class HttpResponse:
    status: int
    url: str
    text: str
    headers: Dict[str, str]
    encoding: Optional[str] = None
    history: Optional[List[HttpHistoryItem]] = None
    content: Optional[bytes] = None


class HttpClientPort(ABC):
    @abstractmethod
    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        form_list: Optional[List[Tuple[str, str]]] = None,
        allow_redirects: Optional[bool] = None,
    ) -> HttpResponse:
        ...

    @abstractmethod
    def snapshot_cookies(self) -> List[Dict[str, object]]:
        ...
