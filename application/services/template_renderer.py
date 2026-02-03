from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple


class TemplateRenderError(Exception):
    pass


@dataclass(frozen=True)
class RenderSources:
    vars: Dict[str, Any]
    state: Dict[str, Any]
    secrets: Dict[str, Any]
    last: Dict[str, Any]


class TemplateRenderer:
    """
    ${vars.xxx}, ${state.xxx}, ${secrets.xxx}, ${last.xxx} を展開する。
    - ドット参照対応: ${vars.login_hidden.token}
    - [*] 展開対応: list をそのまま返す（FormComposer が展開処理を行う）
      例: ${vars.dates[*]} => ["2026/02/02", "2026/04/13"]
    """

    def render_form_list(self, form_list: List[Tuple[str, str]], src: RenderSources) -> List[Tuple[str, Any]]:
        """
        form_list の各値をレンダリング。
        値が list の場合はそのまま list で返す（FormComposer が展開処理を行う）
        """
        out: List[Tuple[str, Any]] = []
        for k, v in form_list:
            rendered_key = self._render_str_scalar(k, src)
            rendered_value = self._render_value(v, src)
            out.append((rendered_key, rendered_value))
        return out

    def _render_value(self, s: str, src: RenderSources) -> Any:
        """
        値をレンダリング。listの場合はlistのまま返す。
        """
        if s is None:
            return ""
        if "${" not in s:
            return s

        # テンプレートが1つだけで、かつ全体がテンプレートの場合
        if s.startswith("${") and s.endswith("}") and s.count("${") == 1:
            expr = s[2:-1].strip()
            value = self._eval(expr, src)
            # list の場合はそのまま返す（FormComposer が展開）
            if isinstance(value, list):
                return value
            return "" if value is None else str(value)

        # 複数埋め込みまたは部分埋め込みの場合は文字列化
        return self._render_str_scalar(s, src)

    def _render_str_scalar(self, s: str, src: RenderSources) -> str:
        """
        文字列として展開（list は join される）
        """
        if s is None:
            return ""
        if "${" not in s:
            return s

        # 複数埋め込みを順に処理
        result = ""
        i = 0
        while i < len(s):
            start = s.find("${", i)
            if start < 0:
                result += s[i:]
                break
            result += s[i:start]
            end = s.find("}", start + 2)
            if end < 0:
                raise TemplateRenderError(f"unclosed template: {s}")
            expr = s[start + 2 : end].strip()
            value = self._eval(expr, src)

            if isinstance(value, list):
                # 文字列コンテキストでは join
                value = ",".join("" if x is None else str(x) for x in value)

            result += "" if value is None else str(value)
            i = end + 1

        return result

    def _eval(self, expr: str, src: RenderSources) -> Any:
        # expr: vars.xxx / state.xxx / secrets.xxx / last.xxx
        root_name, rest = self._split_root(expr)

        root = {
            "vars": src.vars,
            "state": src.state,
            "secrets": src.secrets,
            "last": src.last,
        }.get(root_name)

        if root is None:
            raise TemplateRenderError(f"unknown root: {root_name}")

        if rest == "":
            return root

        return self._resolve_path(root, rest)

    def _split_root(self, expr: str) -> Tuple[str, str]:
        if "." in expr:
            a, b = expr.split(".", 1)
            return a, b
        return expr, ""

    def _resolve_path(self, obj: Any, path: str) -> Any:
        """
        path examples:
          a.b.c
          items[*].id
          items.0.id
        """
        cur = obj
        parts = path.split(".")
        for p in parts:
            cur = self._resolve_part(cur, p)
        return cur

    def _resolve_part(self, cur: Any, part: str) -> Any:
        # [*]
        if part.endswith("[*]"):
            key = part[:-3]
            arr = self._get_key(cur, key)
            if not isinstance(arr, list):
                raise TemplateRenderError(f"{key} is not list for [*] expansion")
            return arr

        # key[*].x 形式のために、part に [*] が含まれていたら分解
        if "[*]" in part:
            # e.g. items[*] handled above, so here is like items[*]something => invalid
            raise TemplateRenderError(f"invalid [*] usage: {part}")

        # list index
        if part.isdigit():
            idx = int(part)
            if not isinstance(cur, list):
                raise TemplateRenderError(f"index access on non-list: {part}")
            if idx < 0 or idx >= len(cur):
                return ""
            return cur[idx]

        # normal dict key
        return self._get_key(cur, part)

    def _get_key(self, cur: Any, key: str) -> Any:
        if isinstance(cur, dict):
            return cur.get(key, "")
        # object attribute access (optional)
        if hasattr(cur, key):
            return getattr(cur, key)
        return ""
