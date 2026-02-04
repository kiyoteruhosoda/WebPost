from __future__ import annotations

from api.main import RunScenarioRequest, _build_secret_provider_resolver
from infrastructure.secrets.dict_secret_provider import DictSecretProvider
from infrastructure.secrets.env_secret_provider import EnvSecretProvider
from fastapi import HTTPException


def test_resolve_defaults_to_inline_provider() -> None:
    # Arrange
    request = RunScenarioRequest(vars={}, secrets={"token": "value"}, secret_ref=None)
    resolver = _build_secret_provider_resolver()

    # Act
    provider = resolver.resolve(request)

    # Assert
    assert isinstance(provider, DictSecretProvider)
    assert provider.get() == {"token": "value"}


def test_resolve_env_provider(monkeypatch) -> None:
    # Arrange
    monkeypatch.setenv("FUNNAVI_FULLTIME_ID", "fulltime")
    monkeypatch.setenv("FUNNAVI_PASSWORD", "secret")
    request = RunScenarioRequest(vars={}, secrets={}, secret_ref="env")
    resolver = _build_secret_provider_resolver()

    # Act
    provider = resolver.resolve(request)

    # Assert
    assert isinstance(provider, EnvSecretProvider)
    assert provider.get() == {
        "FUNNAVI_FULLTIME_ID": "fulltime",
        "FUNNAVI_PASSWORD": "secret",
    }


def test_resolve_unknown_secret_ref_raises() -> None:
    # Arrange
    request = RunScenarioRequest(vars={}, secrets={}, secret_ref="unknown")
    resolver = _build_secret_provider_resolver()

    # Act / Assert
    try:
        resolver.resolve(request)
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "Unknown secret_ref: unknown"
        return
    raise AssertionError("Expected HTTPException to be raised")
