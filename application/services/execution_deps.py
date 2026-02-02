# application/services/execution_deps.py
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, Protocol

from application.ports.logger import LoggerPort


class SecretProviderPort(Protocol):
    def get(self) -> Dict[str, Any]:
        ...


class UrlResolverPort(Protocol):
    def resolve_url(self, url: str) -> str:
        ...


@dataclass(frozen=True)
class ExecutionDeps:
    secret_provider: SecretProviderPort
    url_resolver: UrlResolverPort
    logger: LoggerPort

    def resolve_url(self, url: str) -> str:
        return self.url_resolver.resolve_url(url)

    # ★追加：logger 差し替えのためのコピー生成
    def with_logger(self, logger: LoggerPort) -> "ExecutionDeps":
        return replace(self, logger=logger)
