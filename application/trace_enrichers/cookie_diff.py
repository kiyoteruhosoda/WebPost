# application/trace_enrichers/cookie_diff.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from application.http_trace import HttpTrace
from application.http_trace_enricher import HttpTraceEnricher
from application.services.execution_deps import ExecutionDeps


def _cookie_index(items: List[Dict[str, object]]) -> Dict[Tuple[str, str, str], Dict[str, object]]:
    """
    Key by (name, domain, path). Value is full cookie dict (value included).
    """
    idx: Dict[Tuple[str, str, str], Dict[str, object]] = {}
    for c in items or []:
        name = str(c.get("name", ""))
        domain = str(c.get("domain", ""))
        path = str(c.get("path", ""))
        idx[(name, domain, path)] = c
    return idx


@dataclass(frozen=True)
class CookieDiff:
    added: Set[str]
    removed: Set[str]
    changed: Set[str]


def _diff(before: List[Dict[str, object]], after: List[Dict[str, object]]) -> CookieDiff:
    b = _cookie_index(before)
    a = _cookie_index(after)

    b_keys = set(b.keys())
    a_keys = set(a.keys())

    added_keys = a_keys - b_keys
    removed_keys = b_keys - a_keys
    common = a_keys & b_keys

    # Names only (no values)
    added_names = {k[0] for k in added_keys}
    removed_names = {k[0] for k in removed_keys}

    changed_names: Set[str] = set()
    for k in common:
        bv = b[k].get("value")
        av = a[k].get("value")
        # do NOT log values; only detect change
        if bv != av:
            changed_names.add(k[0])

    return CookieDiff(
        added=set(sorted(added_names)),
        removed=set(sorted(removed_names)),
        changed=set(sorted(changed_names)),
    )


class CookieDiffLogger(HttpTraceEnricher):
    def enrich_and_log(self, trace: HttpTrace, deps: ExecutionDeps) -> None:
        before = trace.cookies_before.items if trace.cookies_before else []
        after = trace.cookies_after.items if trace.cookies_after else []

        d = _diff(before, after)

        deps.logger.info(
            "http.cookie_diff",
            step_id=trace.step_id,
            added=sorted(list(d.added)),
            removed=sorted(list(d.removed)),
            changed=sorted(list(d.changed)),
        )
