from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Protocol, Any

from domain.run import RunContext


class ScrapeTargetError(Exception):
    pass


class ScrapeTarget(Protocol):
    def save(self, ctx: RunContext, key: str, value: Any) -> None:
        ...


@dataclass(frozen=True)
class VarsTarget:
    def save(self, ctx: RunContext, key: str, value: Any) -> None:
        ctx.vars[key] = value


@dataclass(frozen=True)
class StateTarget:
    def save(self, ctx: RunContext, key: str, value: Any) -> None:
        ctx.state[key] = value


@dataclass(frozen=True)
class ScrapeTargetRegistry:
    targets: Dict[str, ScrapeTarget]

    @classmethod
    def default(cls) -> "ScrapeTargetRegistry":
        return cls(targets={"vars": VarsTarget(), "state": StateTarget()})

    def get(self, target_name: str) -> ScrapeTarget:
        if target_name not in self.targets:
            raise ScrapeTargetError(f"unsupported scrape save_to: {target_name}")
        return self.targets[target_name]
