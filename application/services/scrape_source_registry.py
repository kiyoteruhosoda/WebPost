from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Protocol

from domain.run import RunContext


class ScrapeSourceError(Exception):
    pass


class ScrapeSource(Protocol):
    def get_text(self, ctx: RunContext) -> str:
        ...


@dataclass(frozen=True)
class LastTextSource:
    def get_text(self, ctx: RunContext) -> str:
        if not ctx.last or not ctx.last.text:
            raise ScrapeSourceError("scrape requires ctx.last.text (no previous response)")
        return ctx.last.text


@dataclass(frozen=True)
class ScrapeSourceRegistry:
    sources: Dict[str, ScrapeSource]

    @classmethod
    def default(cls) -> "ScrapeSourceRegistry":
        return cls(sources={"last.text": LastTextSource()})

    def get(self, source_name: str) -> ScrapeSource:
        if source_name not in self.sources:
            raise ScrapeSourceError(f"unsupported scrape source: {source_name}")
        return self.sources[source_name]
