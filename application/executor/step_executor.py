# application/executor/step_executor.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import time
import uuid

from application.executor.handler_registry import HandlerRegistry
from application.outcome import StepOutcome
from application.services.execution_deps import ExecutionDeps
from domain.run import RunContext
from domain.steps.base import Step, OnErrorRule, RetryPolicy


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    failed_step_id: Optional[str] = None
    error_message: Optional[str] = None


class StepExecutor:
    def __init__(self, registry: HandlerRegistry):
        self._registry = registry

    def execute(self, steps: List[Step], ctx: RunContext, deps: ExecutionDeps) -> ExecutionResult:
        # ★run_id を付与（呼び元が指定していれば尊重）
        if not getattr(ctx, "run_id", ""):
            ctx.run_id = uuid.uuid4().hex

        # ★logger に run_id を bind して、以後のログに自動付与
        deps = deps.with_logger(deps.logger.bind(run_id=ctx.run_id))

        # ステップのインデックスマップを作成（goto用）
        step_index_map = {s.id: i for i, s in enumerate(steps)}
        
        i = 0
        while i < len(steps):
            step = steps[i]
            
            if getattr(step, "enabled", True) is False:
                i += 1
                continue

            # ステップを実行（リトライ付き）
            outcome = self._execute_step_with_retry(step, ctx, deps)

            if outcome.ok:
                i += 1
                continue

            # エラー処理
            action = self._resolve_error_action(step, ctx, deps)
            
            if action == "abort":
                return ExecutionResult(
                    ok=False,
                    failed_step_id=step.id,
                    error_message=outcome.error_message,
                )
            elif action == "retry":
                # リトライは _execute_step_with_retry で処理済み
                # それでも失敗した場合はabort
                return ExecutionResult(
                    ok=False,
                    failed_step_id=step.id,
                    error_message=f"Max retries exceeded: {outcome.error_message}",
                )
            elif action.startswith("goto:"):
                # goto処理
                goto_step_id = action[5:]
                if goto_step_id not in step_index_map:
                    deps.logger.error("goto.target_not_found", step_id=step.id, goto_step_id=goto_step_id)
                    return ExecutionResult(
                        ok=False,
                        failed_step_id=step.id,
                        error_message=f"goto target not found: {goto_step_id}",
                    )
                deps.logger.info("goto.jumping", from_step=step.id, to_step=goto_step_id)
                i = step_index_map[goto_step_id]
            else:
                # 未知のアクション
                return ExecutionResult(
                    ok=False,
                    failed_step_id=step.id,
                    error_message=f"Unknown error action: {action}",
                )

        return ExecutionResult(ok=True)

    def _execute_step_with_retry(self, step: Step, ctx: RunContext, deps: ExecutionDeps) -> StepOutcome:
        """ステップをリトライポリシーに従って実行"""
        handler = self._registry.get_handler(step)
        retry_policy: RetryPolicy = getattr(step, "retry", None) or RetryPolicy()
        
        max_attempts = retry_policy.max + 1  # max=2 なら 3回試行（初回 + リトライ2回）
        backoff_sec = retry_policy.backoff_sec or []

        for attempt in range(max_attempts):
            if attempt > 0:
                # リトライ前の待機
                wait_sec = backoff_sec[attempt - 1] if (attempt - 1) < len(backoff_sec) else 1
                deps.logger.info(
                    "step.retry",
                    step_id=step.id,
                    attempt=attempt + 1,
                    max_attempts=max_attempts,
                    wait_sec=wait_sec,
                )
                time.sleep(wait_sec)

            deps.logger.info(
                "step.start",
                step_id=step.id,
                step_type=type(step).__name__,
                attempt=attempt + 1,
            )
            t0 = time.perf_counter()

            outcome: StepOutcome = handler.handle(step, ctx, deps)

            deps.logger.info(
                "step.end",
                step_id=step.id,
                ok=(outcome is not None and outcome.ok),
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
                attempt=attempt + 1,
            )

            if outcome is None:
                raise RuntimeError(
                    f"Handler returned None: handler={type(handler).__name__}, step={step.id} ({type(step).__name__})"
                )

            if outcome.ok:
                return outcome

        # すべてのリトライが失敗
        return outcome

    def _resolve_error_action(self, step: Step, ctx: RunContext, deps: ExecutionDeps) -> str:
        """
        on_error ルールを評価してアクションを決定
        戻り値: "abort" | "retry" | "goto:<step_id>"
        """
        on_error_rules: List[OnErrorRule] = getattr(step, "on_error", []) or []
        
        for rule in on_error_rules:
            # when_expr が None なら else 節（常にマッチ）
            if rule.when_expr is None:
                return self._rule_to_action(rule)

            # 条件式を評価（簡易実装）
            if self._eval_condition(rule.when_expr, ctx, deps):
                return self._rule_to_action(rule)

        # デフォルトはabort
        return "abort"

    def _rule_to_action(self, rule: OnErrorRule) -> str:
        """OnErrorRule をアクション文字列に変換"""
        if rule.action == "goto" and rule.goto_step_id:
            return f"goto:{rule.goto_step_id}"
        return rule.action

    def _eval_condition(self, expr: str, ctx: RunContext, deps: ExecutionDeps) -> bool:
        """
        条件式を評価（簡易実装）
        例: "${last.status}==401"
        """
        try:
            # テンプレート展開
            from application.services.template_renderer import TemplateRenderer, RenderSources
            
            renderer = TemplateRenderer()
            src = RenderSources(
                vars=ctx.vars,
                state=ctx.state,
                secrets=deps.secrets,
                last=self._last_to_dict(ctx.last),
            )
            
            rendered = renderer._render_str_scalar(expr, src)
            
            # 簡易評価: "値==401", "値>=500" など
            if "==" in rendered:
                left, right = rendered.split("==", 1)
                return left.strip() == right.strip()
            elif ">=" in rendered:
                left, right = rendered.split(">=", 1)
                try:
                    return int(left.strip()) >= int(right.strip())
                except ValueError:
                    return False
            elif "<=" in rendered:
                left, right = rendered.split("<=", 1)
                try:
                    return int(left.strip()) <= int(right.strip())
                except ValueError:
                    return False
            
            # それ以外は真偽値として評価
            return bool(rendered and rendered.lower() not in ("false", "0", ""))
            
        except Exception as e:
            deps.logger.debug("condition.eval_failed", expr=expr, error=str(e))
            return False

    def _last_to_dict(self, last) -> dict:
        if last is None:
            return {}
        return {
            "status": getattr(last, "status", 0),
            "url": getattr(last, "url", ""),
            "text": getattr(last, "text", ""),
            "headers": getattr(last, "headers", {}),
        }
