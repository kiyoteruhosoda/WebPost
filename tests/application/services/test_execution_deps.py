# tests/application/services/test_execution_deps.py
import pytest
from application.services.execution_deps import ExecutionDeps


class MockSecretProvider:
    def __init__(self, secrets=None):
        self.secrets = secrets or {"api_key": "secret123"}
    
    def get(self):
        return self.secrets


class MockUrlResolver:
    def __init__(self, base_url="https://example.com"):
        self.base_url = base_url
    
    def resolve_url(self, url):
        if url.startswith("http"):
            return url
        return f"{self.base_url}{url}"


class MockLogger:
    def __init__(self):
        self.logs = []
        self.bound_context = {}
    
    def info(self, message, **kwargs):
        self.logs.append({"message": message, **kwargs})
    
    def bind(self, **kwargs):
        new_logger = MockLogger()
        new_logger.logs = self.logs
        new_logger.bound_context = {**self.bound_context, **kwargs}
        return new_logger


class TestExecutionDeps:
    def test_create_execution_deps(self):
        secret_provider = MockSecretProvider()
        url_resolver = MockUrlResolver()
        logger = MockLogger()
        
        deps = ExecutionDeps(
            secret_provider=secret_provider,
            url_resolver=url_resolver,
            logger=logger
        )
        
        assert deps.secret_provider is secret_provider
        assert deps.url_resolver is url_resolver
        assert deps.logger is logger

    def test_resolve_url_delegates_to_resolver(self):
        secret_provider = MockSecretProvider()
        url_resolver = MockUrlResolver(base_url="https://api.example.com")
        logger = MockLogger()
        
        deps = ExecutionDeps(
            secret_provider=secret_provider,
            url_resolver=url_resolver,
            logger=logger
        )
        
        result = deps.resolve_url("/api/users")
        assert result == "https://api.example.com/api/users"

    def test_resolve_url_with_absolute_url(self):
        secret_provider = MockSecretProvider()
        url_resolver = MockUrlResolver()
        logger = MockLogger()
        
        deps = ExecutionDeps(
            secret_provider=secret_provider,
            url_resolver=url_resolver,
            logger=logger
        )
        
        result = deps.resolve_url("https://other.com/path")
        assert result == "https://other.com/path"

    def test_with_logger_creates_new_deps(self):
        secret_provider = MockSecretProvider()
        url_resolver = MockUrlResolver()
        logger1 = MockLogger()
        
        deps1 = ExecutionDeps(
            secret_provider=secret_provider,
            url_resolver=url_resolver,
            logger=logger1
        )
        
        logger2 = MockLogger()
        deps2 = deps1.with_logger(logger2)
        
        # Should create a new instance
        assert deps2 is not deps1
        assert deps2.logger is logger2
        # Other fields should be preserved
        assert deps2.secret_provider is secret_provider
        assert deps2.url_resolver is url_resolver

    def test_with_logger_preserves_original_deps(self):
        secret_provider = MockSecretProvider()
        url_resolver = MockUrlResolver()
        logger1 = MockLogger()
        
        deps1 = ExecutionDeps(
            secret_provider=secret_provider,
            url_resolver=url_resolver,
            logger=logger1
        )
        
        logger2 = MockLogger()
        deps2 = deps1.with_logger(logger2)
        
        # Original should be unchanged
        assert deps1.logger is logger1

    def test_with_logger_can_bind_context(self):
        secret_provider = MockSecretProvider()
        url_resolver = MockUrlResolver()
        logger1 = MockLogger()
        
        deps1 = ExecutionDeps(
            secret_provider=secret_provider,
            url_resolver=url_resolver,
            logger=logger1
        )
        
        # Bind context to logger
        logger2 = logger1.bind(run_id="test-run-123")
        deps2 = deps1.with_logger(logger2)
        
        assert deps2.logger is logger2
        assert deps2.logger.bound_context == {"run_id": "test-run-123"}

    def test_execution_deps_frozen(self):
        secret_provider = MockSecretProvider()
        url_resolver = MockUrlResolver()
        logger = MockLogger()
        
        deps = ExecutionDeps(
            secret_provider=secret_provider,
            url_resolver=url_resolver,
            logger=logger
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError
            deps.logger = MockLogger()

    def test_secret_provider_protocol(self):
        secret_provider = MockSecretProvider(secrets={"password": "secret", "token": "abc123"})
        url_resolver = MockUrlResolver()
        logger = MockLogger()
        
        deps = ExecutionDeps(
            secret_provider=secret_provider,
            url_resolver=url_resolver,
            logger=logger
        )
        
        secrets = deps.secret_provider.get()
        assert secrets == {"password": "secret", "token": "abc123"}

    def test_url_resolver_protocol(self):
        secret_provider = MockSecretProvider()
        url_resolver = MockUrlResolver(base_url="https://test.com")
        logger = MockLogger()
        
        deps = ExecutionDeps(
            secret_provider=secret_provider,
            url_resolver=url_resolver,
            logger=logger
        )
        
        resolved = deps.url_resolver.resolve_url("/path")
        assert resolved == "https://test.com/path"
