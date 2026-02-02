# application/handlers/http_handler.py
from __future__ import annotations

import re
import hashlib
from collections import Counter
from typing import Any, Dict, List, Tuple, Optional

from bs4 import BeautifulSoup

from application.handlers.base import StepHandler
from application.outcome import StepOutcome
from application.ports.http_client import HttpClientPort
from application.services.execution_deps import ExecutionDeps
from application.services.form_composer import FormComposer
from application.services.redactor import mask_dict, mask_pairs
from application.services.template_renderer import RenderSources, TemplateRenderer
from domain.run import LastResponse, RunContext
from domain.steps.http import HttpStep

from application.http_trace import HttpTrace, HttpResponseMeta, CookieSnapshot
from application.http_trace_emitter import HttpTraceEmitter
from application.trace_enrichers.core import HttpCoreTraceLogger
from application.trace_enrichers.html_signals import HtmlSignalLogger
from application.trace_enrichers.html_saver import HtmlSaver
from typing import List, Tuple

def _try_extract_title(html: str) -> Optional[str]:
    try:
        soup = BeautifulSoup(html, "html.parser")
        return soup.title.get_text(strip=True) if soup.title else None
    except Exception:
        return None

# application/handlers/http_handler.py
def _decode_html_bytes(raw: Optional[bytes], headers: Dict[str, str], fallback_text: str) -> tuple[str, Optional[str]]:
    """
    raw bytes + headers からHTMLを復元する。
    戻り値: (decoded_html, decided_encoding)
    """
    if not raw:
        return fallback_text, None

    # 1) Content-Type の charset を優先
    ctype = (headers or {}).get("Content-Type") or (headers or {}).get("content-type") or ""
    m = re.search(r"charset\s*=\s*([^\s;]+)", ctype, re.I)
    if m:
        enc = m.group(1).strip().strip('"').strip("'")
        try:
            return raw.decode(enc, errors="replace"), enc
        except Exception:
            pass

    # 2) ありがちな日本語サイトのフォールバック（cp932優先）
    for enc in ("cp932", "shift_jis", "windows-31j", "utf-8"):
        try:
            return raw.decode(enc, errors="replace"), enc
        except Exception:
            continue

    # 3) 最後の手段
    return raw.decode("utf-8", errors="replace"), "utf-8"

def _detect_collisions(base_form: List[Tuple[str, str]], merged_dict: Dict[str, Any]) -> List[str]:
    base_keys = [k for k, _ in (base_form or [])]
    merged_keys = list((merged_dict or {}).keys())
    return sorted(set(base_keys) & set(merged_keys))


def _dup_keys(pairs: List[Tuple[str, str]]) -> List[str]:
    c = Counter([k for k, _ in (pairs or [])])
    return sorted([k for k, v in c.items() if v > 1])

    
def _dedupe_pairs_last_wins(pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    # 同一キーが複数ある場合、最後の値を採用（ブラウザの送信挙動に近い）
    last_index = {}
    for i, (k, _v) in enumerate(pairs):
        last_index[k] = i
    return [(k, v) for i, (k, v) in enumerate(pairs) if last_index.get(k) == i]

class HttpStepHandler(StepHandler):
    def __init__(self, http_client: HttpClientPort, renderer: TemplateRenderer):
        self._http = http_client
        self._renderer = renderer
        self._composer = FormComposer(renderer)

        self._trace = HttpTraceEmitter([
            HttpCoreTraceLogger(),
            HtmlSignalLogger(),
            HtmlSaver(out_dir="tmp/http"),
        ])

    def supports(self, step) -> bool:
        return isinstance(step, HttpStep)

    def handle(self, step: HttpStep, ctx: RunContext, deps: ExecutionDeps) -> StepOutcome:
        try:
            url = deps.resolve_url(step.request.url)

            last_dict: Dict[str, Any] = {}
            if ctx.last:
                last_dict = {
                    "status": ctx.last.status,
                    "url": ctx.last.url,
                    "text": ctx.last.text,
                    "headers": ctx.last.headers,
                }

            secrets = deps.secret_provider.get()

            src = RenderSources(
                vars=ctx.vars,
                state=ctx.state,
                secrets=secrets,
                last=last_dict,
            )

            # form_list 合成（テンプレ展開 + vars merge）
            base_form = step.request.form_list or []
            merge_from = getattr(step.request, "merge_from_vars", None)

            composed = self._composer.compose(
                form_list=base_form,
                src=src,
                vars_dict=ctx.vars,
                merge_from_vars=merge_from,
            )

            deduped_form = _dedupe_pairs_last_wins(composed.form_list)

            # DEBUG: form / headers はマスクしてログ
            deps.logger.debug(
                "http.form_composed",
                step_id=step.id,
                method=step.request.method,
                url=url,
                merged_from=composed.merged_from,
                merged_count=composed.merged_count,
                duplicate_keys=_dup_keys(composed.form_list),
                collision_keys=_detect_collisions(base_form, ctx.vars.get(merge_from, {}) if merge_from else {}),
                form=mask_pairs(composed.form_list),
                headers=mask_dict(step.request.headers or {}),
            )

            deps.logger.info("http.client_impl", cls=type(self._http).__name__, module=type(self._http).__module__)

            cookies_before = CookieSnapshot(items=self._http.snapshot_cookies())

            # ログインPOSTだけ redirect を切りたいならここで条件分岐
            allow_redirects: Optional[bool] = None
            if step.request.method.upper() == "POST":
                # 切り分け優先：まず False 推奨（必要なら後でTrueに戻す）
                allow_redirects = False

            resp = self._http.request(
                method=step.request.method,
                url=url,
                headers=step.request.headers,
                form_list=deduped_form,
                allow_redirects=allow_redirects,
            )

            cookies_after = CookieSnapshot(items=self._http.snapshot_cookies())

            raw = resp.content
            body, decided_enc = _decode_html_bytes(raw, resp.headers or {}, resp.text or "")
            body_sha = hashlib.sha256(raw).hexdigest() if raw is not None else hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()

            # history 正規化
            hist = []
            for h in (resp.history or []):
                hist.append({
                    "status": h.status,
                    "url": h.url,
                    "location": h.location,
                    "set_cookie": bool(h.set_cookie),
                })

            trace = HttpTrace(
                run_id=ctx.run_id,
                step_id=step.id,
                method=step.request.method,
                url=url,
                request_headers=step.request.headers or {},
                request_form=deduped_form,
                merged_from=composed.merged_from,
                merged_count=composed.merged_count,
                collision_keys=_detect_collisions(base_form, ctx.vars.get(merge_from, {}) if merge_from else {}),
                cookies_before=cookies_before,
                cookies_after=cookies_after,
                response=HttpResponseMeta(
                    status=resp.status,
                    url=resp.url,
                    headers=resp.headers or {},
                    encoding=decided_enc or getattr(resp, "encoding", None),
                    content_type=(resp.headers or {}).get("Content-Type"),
                    history=hist,
                    body_len=len(body),
                    body_sha256=body_sha,
                ),
                text_head=body[:4000],
                html_title=_try_extract_title(body),
                full_text=body,
                raw_bytes=getattr(resp, "content", None),
            )
            self._trace.emit(trace, deps)

            # 既存ログ（簡易）
            deps.logger.info(
                "http.response",
                step_id=step.id,
                status=resp.status,
                final_url=resp.url,
                text_head=body[:200],
            )

            ctx.last = LastResponse(
                status=resp.status,
                url=resp.url,
                text=body,
                headers=resp.headers,
            )
            return StepOutcome(ok=True)

        except Exception as e:
            deps.logger.error(
                "http.step_failed",
                step_id=getattr(step, "id", "unknown"),
                error=str(e),
            )
            return StepOutcome(ok=False, error_message=str(e))
