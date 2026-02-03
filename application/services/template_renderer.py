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
    - [*] 展開対応: いまは form_list の値として使うことを想定（joinする）
      例: ${vars.items[*].id} => "1,2,3" （デフォルト）
    """

    def render_form_list(self, form_list: List[Tuple[str, str]], src: RenderSources) -> List[Tuple[str, str]]:
        out: List[Tuple[str, str]] = []
        for k, v in form_list:
            out.append((self._render_str(k, src), self._render_str(v, src)))
        return out

    def render_value(self, value: Any, src: RenderSources) -> Any:
        """
        Public wrapper for rendering a single value.
        Reason: Result steps need a supported method for template expansion.
        Impact: Only template strings are expanded; non-string values pass through.
        """
        if isinstance(value, str) or value is None:
            return self._render_str(value, src)
        return value

    def _render_str(self, s: str, src: RenderSources) -> str:
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
                # form value としては join して文字列化
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
