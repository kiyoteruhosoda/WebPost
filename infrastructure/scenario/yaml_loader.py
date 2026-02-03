# infrastructure/scenario/yaml_loader.py
"""
YAMLシナリオファイルからScenarioドメインオブジェクトを生成
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from domain.scenario import (
    Scenario,
    ScenarioMeta,
    ScenarioInputs,
    ScenarioDefaults,
    HttpDefaults,
)
from domain.steps.base import Step, RetryPolicy, OnErrorRule
from domain.steps.http import HttpStep, HttpRequestSpec
from domain.steps.scrape import ScrapeStep
from domain.steps.assertion import AssertStep, ConditionSpec
from domain.steps.result import ResultStep


class ScenarioLoadError(Exception):
    pass


class YamlScenarioLoader:
    """YAMLファイルからScenarioをロード"""

    def load_from_file(self, path: str) -> Scenario:
        """YAMLファイルからScenarioをロード"""
        p = Path(path)
        if not p.exists():
            raise ScenarioLoadError(f"Scenario file not found: {path}")

        with p.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            raise ScenarioLoadError(f"Scenario file is empty: {path}")

        if not isinstance(data, dict):
            raise ScenarioLoadError(f"Scenario file is invalid: {path}")

        return self.load_from_dict(data)

    def load_from_dict(self, data: Dict[str, Any]) -> Scenario:
        """dict からScenarioをロード"""
        meta = self._load_meta(data.get("meta", {}))
        inputs = self._load_inputs(data.get("inputs", {}))
        defaults = self._load_defaults(data.get("defaults", {}))
        steps = self._load_steps(data.get("steps", []))

        return Scenario(
            meta=meta,
            inputs=inputs,
            defaults=defaults,
            steps=steps,
        )

    def _load_meta(self, data: Dict[str, Any]) -> ScenarioMeta:
        return ScenarioMeta(
            id=data.get("id", 0),
            name=data.get("name", ""),
            version=data.get("version", 1),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            user_agent=data.get("user_agent", "ScenarioRunner/1.0"),
        )

    def _load_inputs(self, data: Dict[str, Any]) -> ScenarioInputs:
        return ScenarioInputs(
            required=data.get("required", []),
            optional=data.get("optional", []),
        )

    def _load_defaults(self, data: Dict[str, Any]) -> ScenarioDefaults:
        http_data = data.get("http")
        http_defaults = None
        if http_data:
            http_defaults = HttpDefaults(
                base_url=http_data.get("base_url", ""),
                timeout_sec=http_data.get("timeout_sec", 20),
                headers=http_data.get("headers", {}),
            )

        return ScenarioDefaults(http=http_defaults)

    def _load_steps(self, steps_data: List[Dict[str, Any]]) -> List[Step]:
        steps: List[Step] = []
        for step_data in steps_data:
            step = self._load_step(step_data)
            if step:
                steps.append(step)
        return steps

    def _load_step(self, data: Dict[str, Any]) -> Optional[Step]:
        """ステップをtype別にロード"""
        step_type = data.get("type", "").lower()
        step_id = data.get("id", "unknown")

        # 共通フィールド
        enabled = data.get("enabled", True)
        retry = self._load_retry(data.get("retry", {}))
        on_error = self._load_on_error(data.get("on_error", []))

        common_kwargs = {
            "id": step_id,
            "name": step_id,  # nameはidと同じにする
            "enabled": enabled,
            "retry": retry,
            "on_error": on_error,
        }

        if step_type == "http":
            return self._load_http_step(data, common_kwargs)
        if step_type == "scrape":
            return self._load_scrape_step(data, common_kwargs)
        if step_type == "assert":
            return self._load_assert_step(data, common_kwargs)
        if step_type == "result":
            return self._load_result_step(data, common_kwargs)

        # 未知のステップタイプはスキップ（またはエラー）
        return None

    def _load_retry(self, data: Dict[str, Any]) -> RetryPolicy:
        if not data:
            return RetryPolicy()
        return RetryPolicy(
            max=data.get("max", 0),
            backoff_sec=data.get("backoff_sec", []),
        )

    def _load_on_error(self, rules_data: List[Dict[str, Any]]) -> List[OnErrorRule]:
        rules: List[OnErrorRule] = []
        for rule_data in rules_data:
            rule = OnErrorRule(
                when_expr=rule_data.get("expr"),
                action=rule_data.get("action", "abort"),
                goto_step_id=rule_data.get("goto_step_id"),
            )
            rules.append(rule)
        return rules

    def _load_http_step(self, data: Dict[str, Any], common: Dict[str, Any]) -> HttpStep:
        req_data = data.get("request", {})

        # form_listをロード
        form_list = []
        for item in req_data.get("form_list", []):
            if isinstance(item, list) and len(item) >= 2:
                form_list.append((item[0], item[1]))

        request = HttpRequestSpec(
            method=req_data.get("method", "GET"),
            url=req_data.get("url", ""),
            headers=req_data.get("headers"),
            form_list=form_list if form_list else None,
            merge_from_vars=req_data.get("merge_from_vars"),
        )

        return HttpStep(
            request=request,
            save_as_last=data.get("save_as_last", True),
            **common,
        )

    def _load_scrape_step(self, data: Dict[str, Any], common: Dict[str, Any]) -> ScrapeStep:
        return ScrapeStep(
            command=data.get("command", ""),
            save_as=data.get("save_as", ""),
            selector=data.get("selector"),
            attr=data.get("attr"),
            multiple=data.get("multiple", False),
            label=data.get("label"),
            **common,
        )

    def _load_assert_step(self, data: Dict[str, Any], common: Dict[str, Any]) -> AssertStep:
        conditions = []
        for cond_data in data.get("conditions", []):
            conditions.append(ConditionSpec(expr=cond_data.get("expr", "")))

        return AssertStep(
            conditions=conditions,
            **common,
        )

    def _load_result_step(self, data: Dict[str, Any], common: Dict[str, Any]) -> ResultStep:
        return ResultStep(
            fields=data.get("fields", {}),
            **common,
        )
