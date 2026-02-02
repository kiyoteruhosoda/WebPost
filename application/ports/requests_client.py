# application/ports/requests_client.py
from __future__ import annotations

import requests
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from application.ports.http_client import HttpResponse, HttpHistoryItem


class RequestsSessionHttpClient:
    def __init__(self, base_headers: Optional[Dict[str, str]] = None, timeout_sec: int = 20):
        self._session = requests.Session()
        self._base_headers = base_headers or {}
        self._timeout = timeout_sec

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        form_list: Optional[List[Tuple[str, str]]] = None,
        allow_redirects: Optional[bool] = None,
    ) -> HttpResponse:
        merged = dict(self._base_headers)
        if headers:
            merged.update(headers)

        # requests のデフォルトは True。NoneならTrueとして扱う
        follow = True if allow_redirects is None else bool(allow_redirects)

        resp = self._session.request(
            method=method.upper(),
            url=url,
            headers=merged,
            data=form_list,              # list[tuple] OK、同名キー複数OK
            timeout=self._timeout,
            allow_redirects=follow,
        )

        history_items: List[HttpHistoryItem] = []
        for h in resp.history or []:
            history_items.append(
                HttpHistoryItem(
                    status=h.status_code,
                    url=str(h.url),
                    location=h.headers.get("Location"),
                    set_cookie=h.headers.get("Set-Cookie"),
                )
            )

        return HttpResponse(
            status=resp.status_code,
            url=str(resp.url),
            text=resp.text,
            headers=dict(resp.headers),
            encoding=resp.encoding,
            history=history_items,
            content=resp.content,
        )

    def snapshot_cookies(self) -> List[Dict[str, object]]:
        out: List[Dict[str, object]] = []
        for c in self._session.cookies:
            out.append(
                {
                    "name": c.name,
                    "value": c.value,
                    "domain": c.domain,
                    "path": c.path,
                    "secure": bool(getattr(c, "secure", False)),
                    "expires": getattr(c, "expires", None),
                }
            )
        return out
