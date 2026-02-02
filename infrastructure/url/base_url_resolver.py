# infrastructure/url/base_url_resolver.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaseUrlResolver:
    base_url: str

    def resolve_url(self, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        return self.base_url.rstrip("/") + "/" + url.lstrip("/")
