# application/trace_enrichers/html_signals.py
from __future__ import annotations

import re
from bs4 import BeautifulSoup

from application.http_trace import HttpTrace
from application.http_trace_enricher import HttpTraceEnricher
from application.services.execution_deps import ExecutionDeps


def _get_first_form_action(soup: BeautifulSoup) -> str | None:
    form = soup.find("form")
    if not form:
        return None
    action = form.get("action")
    return str(action) if action is not None else None


def _get_hidden_value(soup: BeautifulSoup, name: str) -> str | None:
    # hidden input name=... の value を取得
    x = soup.find("input", {"type": "hidden", "name": name})
    if not x:
        return None
    v = x.get("value")
    return str(v) if v is not None else ""


class HtmlSignalLogger(HttpTraceEnricher):
    """
    HTMLレスポンスから「画面判定に有効な軽量シグナル」を抽出してログ化する。
    - title, form_action
    - auto_submit, meta_refresh（requestsではJS実行不可のため重要）
    - screenID（画面遷移判定の中核）
    - 必要最小限の hidden（ホワイトリスト）
    """

    # 必要なら増やす（機密性の高いものは入れない）
    _HIDDEN_WHITELIST = [
        "screenID",
        "referrer",
        "state",
        "csrfToken",
        "__RequestVerificationToken",
    ]

    def enrich_and_log(self, trace: HttpTrace, deps: ExecutionDeps) -> None:
        html = trace.full_text or ""
        title = trace.html_title or ""

        # 中間画面っぽいシグナル（requestsはJS実行できない）
        auto_submit = bool(re.search(r"document\.forms?\[0\]\.submit\(\)", html, re.I))
        meta_refresh = bool(re.search(r"<meta[^>]+http-equiv=[\"']refresh", html, re.I))

        action: str | None = None
        screen_id: str | None = None
        hidden_summary: dict[str, str | None] = {}

        try:
            soup = BeautifulSoup(html, "html.parser")
            action = _get_first_form_action(soup)

            # screenID は特別扱い（判定の軸）
            screen_id = _get_hidden_value(soup, "screenID")

            # 主要hiddenだけサマリ
            for k in self._HIDDEN_WHITELIST:
                hidden_summary[k] = _get_hidden_value(soup, k)

        except Exception:
            action = None
            screen_id = None
            hidden_summary = {}

        deps.logger.info(
            "http.html_signals",
            step_id=trace.step_id,
            title=title,
            form_action=action,
            auto_submit=auto_submit,
            meta_refresh=meta_refresh,
            screenID=screen_id,
            hidden_summary=hidden_summary,
        )
