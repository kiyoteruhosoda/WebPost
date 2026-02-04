# application/trace_enrichers/core.py
from __future__ import annotations

from application.http_trace import HttpTrace
from application.http_trace_enricher import HttpTraceEnricher
from application.services.execution_deps import ExecutionDeps
from application.services.redactor import mask_dict, mask_pairs


class HttpCoreTraceLogger(HttpTraceEnricher):
    def enrich_and_log(self, trace: HttpTrace, deps: ExecutionDeps) -> None:
        deps.logger.info(
            "http.request",
            step_id=trace.step_id,
            method=trace.method,
            url=trace.url,
            allow_redirects=trace.allow_redirects,
            headers=mask_dict(trace.request_headers),
            form=mask_pairs(trace.request_form),
            merged_from=trace.merged_from,
            merged_count=trace.merged_count,
            collision_keys=trace.collision_keys,
        )

        deps.logger.info(
            "http.response",
            step_id=trace.step_id,
            status=trace.response.status,
            final_url=trace.response.url,
            headers=mask_dict(trace.response.headers),
            content_type=trace.response.content_type,
            encoding=trace.response.encoding,
            body_len=trace.response.body_len,
            body_sha256=trace.response.body_sha256,
            history=trace.response.history,
            set_cookie=bool(trace.response.headers.get("Set-Cookie")),
            location=trace.response.headers.get("Location"),
        )

        deps.logger.info(
            "http.trace",
            step_id=trace.step_id,
            method=trace.method,
            url=trace.url,
            status=trace.response.status,
            final_url=trace.response.url,
            content_type=trace.response.content_type,
            encoding=trace.response.encoding,
            body_len=trace.response.body_len,
            body_sha256=trace.response.body_sha256,
            history=trace.response.history,
            set_cookie=bool(trace.response.headers.get("Set-Cookie")),
            location=trace.response.headers.get("Location"),
            collision_keys=trace.collision_keys,
        )

        deps.logger.debug(
            "http.request_detail",
            step_id=trace.step_id,
            headers=mask_dict(trace.request_headers),
            form=mask_pairs(trace.request_form),
        )

        deps.logger.debug(
            "http.cookies",
            step_id=trace.step_id,
            cookies_before_count=len(trace.cookies_before.items),
            cookies_after_count=len(trace.cookies_after.items),
        )
