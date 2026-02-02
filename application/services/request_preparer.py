# application/services/request_preparer.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from application.services.execution_deps import ExecutionDeps
from application.services.form_composer import FormComposer, FormComposeResult
from application.services.template_renderer import RenderSources
from domain.run import RunContext
from domain.steps.http import HttpStep


@dataclass(frozen=True)
class PreparedHttpRequest:
    method: str
    url: str
    headers: Dict[str, str]
    form_list: List[Tuple[str, str]]
    compose_result: FormComposeResult


class RequestPreparer:
    """
    Prepare HTTP requests for HttpStepHandler.
    """

    def __init__(self, composer: FormComposer):
        self._composer = composer

    def prepare(self, step: HttpStep, ctx: RunContext, deps: ExecutionDeps) -> PreparedHttpRequest:
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

        headers = dict(step.request.headers or {})

        base_form = step.request.form_list or []
        compose_result = self._composer.compose(
            form_list=base_form,
            src=src,
            vars_dict=ctx.vars,
            merge_from_vars=getattr(step.request, "merge_from_vars", None),
        )

        return PreparedHttpRequest(
            method=step.request.method,
            url=url,
            headers=headers,
            form_list=compose_result.form_list,
            compose_result=compose_result,
        )
