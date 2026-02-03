# application/services/execution_deps.py
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, Protocol, TYPE_CHECKING

from application.ports.logger import LoggerPort

if TYPE_CHECKING:
    from domain.run import RunContext


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

    def eval_condition(self, expr: str, ctx: "RunContext") -> bool:
        """
        Simple condition evaluator for assertion expressions.
        Supports basic comparisons: ==, >=, <=, >, <
        """
        from domain.steps.expr import ExpressionEvaluator
        
        evaluator = ExpressionEvaluator()
        
        # Build context for template resolution
        template_ctx = {}
        if ctx.vars:
            for k, v in ctx.vars.items():
                template_ctx[f"vars.{k}"] = v
        if ctx.state:
            for k, v in ctx.state.items():
                template_ctx[f"state.{k}"] = v
        if ctx.last:
            template_ctx["last.status"] = getattr(ctx.last, "status", 0)
            template_ctx["last.url"] = getattr(ctx.last, "url", "")
            template_ctx["last.text"] = getattr(ctx.last, "text", "")
        
        # Resolve templates in the expression
        resolved = evaluator.resolve(expr, template_ctx)
        
        # Evaluate the condition
        if "==" in resolved:
            left, right = resolved.split("==", 1)
            return left.strip() == right.strip()
        elif ">=" in resolved:
            left, right = resolved.split(">=", 1)
            try:
                return float(left.strip()) >= float(right.strip())
            except (ValueError, TypeError):
                return False
        elif "<=" in resolved:
            left, right = resolved.split("<=", 1)
            try:
                return float(left.strip()) <= float(right.strip())
            except (ValueError, TypeError):
                return False
        elif ">" in resolved:
            left, right = resolved.split(">", 1)
            try:
                return float(left.strip()) > float(right.strip())
            except (ValueError, TypeError):
                return False
        elif "<" in resolved:
            left, right = resolved.split("<", 1)
            try:
                return float(left.strip()) < float(right.strip())
            except (ValueError, TypeError):
                return False
        
        # If no operator, evaluate as boolean
        return bool(resolved and resolved.lower() not in ("false", "0", ""))
