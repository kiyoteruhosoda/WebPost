from __future__ import annotations

from dataclasses import dataclass

from application.handlers.http_handler import HttpStepHandler
from application.ports.http_client import HttpClientPort, HttpResponse
from application.services.execution_deps import ExecutionDeps
from application.services.template_renderer import TemplateRenderer
from domain.run import RunContext
from domain.steps.http import HttpRequestSpec, HttpStep


@dataclass(frozen=True)
class DummySecretProvider:
    def get(self) -> dict:
        return {}


@dataclass(frozen=True)
class DummyUrlResolver:
    def resolve_url(self, url: str) -> str:
        return url


@dataclass(frozen=True)
class DummyLogger:
    def info(self, _message: str, **_kwargs) -> None:
        return None

    def error(self, _message: str, **_kwargs) -> None:
        return None

    def debug(self, _message: str, **_kwargs) -> None:
        return None

    def bind(self, **_kwargs) -> "DummyLogger":
        return self


class DummyHttpClient(HttpClientPort):
    def request(self, method, url, headers=None, form_list=None, allow_redirects=None) -> HttpResponse:
        return HttpResponse(
            status=200,
            url=url,
            text="ok",
            headers={},
            content=b"ok",
        )

    def snapshot_cookies(self):
        return []


def test_http_handler_respects_save_as_last_false() -> None:
    # Arrange
    handler = HttpStepHandler(DummyHttpClient(), TemplateRenderer())
    step = HttpStep(
        id="http-no-last",
        name="http-no-last",
        request=HttpRequestSpec(method="GET", url="https://example.com"),
        save_as_last=False,
    )
    ctx = RunContext(vars={}, state={}, last=None, result={})
    deps = ExecutionDeps(
        secret_provider=DummySecretProvider(),
        url_resolver=DummyUrlResolver(),
        logger=DummyLogger(),
    )

    # Act
    outcome = handler.handle(step, ctx, deps)

    # Assert
    assert outcome.ok is True
    assert ctx.last is None
