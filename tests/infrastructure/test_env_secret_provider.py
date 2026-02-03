# tests/infrastructure/test_env_secret_provider.py
from infrastructure.secrets.env_secret_provider import EnvSecretProvider


def test_get_returns_env_key_names(monkeypatch):
    monkeypatch.setenv("FUNNAVI_FULLTIME_ID", "user-123")
    monkeypatch.setenv("FUNNAVI_PASSWORD", "secret-pass")

    provider = EnvSecretProvider()

    result = provider.get()

    assert result == {
        "FUNNAVI_FULLTIME_ID": "user-123",
        "FUNNAVI_PASSWORD": "secret-pass",
    }
