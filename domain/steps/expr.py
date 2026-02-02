# domain/expr.py
import re
from typing import Any, Dict

class ExpressionEvaluator:
    def resolve(self, template: str, ctx: Dict[str, Any]) -> str:
        # "${vars.x}" 等の最小置換（必要十分に）
        out = template
        for k, v in ctx.items():
            out = out.replace("${" + k + "}", str(v))
        return out

    def matches(self, text: str, pattern: str) -> bool:
        return re.match(pattern, text or "") is not None

    def contains(self, text: str, sub: str) -> bool:
        return (sub in (text or ""))

    def not_contains(self, text: str, sub: str) -> bool:
        return sub not in (text or "")
