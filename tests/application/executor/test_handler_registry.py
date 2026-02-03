# tests/application/executor/test_handler_registry.py
import pytest
from application.executor.handler_registry import HandlerRegistry
from application.handlers.base import StepHandler
from application.outcome import StepOutcome
from domain.steps.base import Step


class DummyStep(Step):
    """A dummy step for testing"""
    pass


class AnotherDummyStep(Step):
    """Another dummy step for testing"""
    pass


class DummyHandler(StepHandler):
    def __init__(self):
        self.call_count = 0
        
    def supports(self, step: Step) -> bool:
        return isinstance(step, DummyStep)
    
    def handle(self, step, ctx, deps):
        self.call_count += 1
        return StepOutcome(ok=True)


class AnotherHandler(StepHandler):
    def __init__(self):
        self.call_count = 0
        
    def supports(self, step: Step) -> bool:
        return isinstance(step, AnotherDummyStep)
    
    def handle(self, step, ctx, deps):
        self.call_count += 1
        return StepOutcome(ok=True)


class TestHandlerRegistry:
    def test_create_registry_with_handlers(self):
        handler1 = DummyHandler()
        handler2 = AnotherHandler()
        registry = HandlerRegistry(handlers=[handler1, handler2])
        assert registry is not None

    def test_get_handler_for_supported_step(self):
        handler = DummyHandler()
        registry = HandlerRegistry(handlers=[handler])
        
        step = DummyStep(id="test-step", name="Test Step")
        result = registry.get_handler(step)
        
        assert result is handler

    def test_get_handler_returns_first_matching_handler(self):
        handler1 = DummyHandler()
        handler2 = DummyHandler()  # Another instance
        registry = HandlerRegistry(handlers=[handler1, handler2])
        
        step = DummyStep(id="test-step", name="Test Step")
        result = registry.get_handler(step)
        
        # Should return the first handler that supports the step
        assert result is handler1

    def test_get_handler_with_multiple_handler_types(self):
        dummy_handler = DummyHandler()
        another_handler = AnotherHandler()
        registry = HandlerRegistry(handlers=[dummy_handler, another_handler])
        
        # Test with DummyStep
        step1 = DummyStep(id="step1", name="Step 1")
        result1 = registry.get_handler(step1)
        assert result1 is dummy_handler
        
        # Test with AnotherDummyStep
        step2 = AnotherDummyStep(id="step2", name="Step 2")
        result2 = registry.get_handler(step2)
        assert result2 is another_handler

    def test_get_handler_raises_error_for_unsupported_step(self):
        handler = DummyHandler()
        registry = HandlerRegistry(handlers=[handler])
        
        # Create a step that is not supported by any handler
        unsupported_step = AnotherDummyStep(id="unsupported", name="Unsupported")
        
        with pytest.raises(RuntimeError, match="No handler found"):
            registry.get_handler(unsupported_step)

    def test_get_handler_empty_registry_raises_error(self):
        registry = HandlerRegistry(handlers=[])
        
        step = DummyStep(id="test-step", name="Test Step")
        
        with pytest.raises(RuntimeError, match="No handler found"):
            registry.get_handler(step)

    def test_handler_called_correctly(self):
        handler = DummyHandler()
        registry = HandlerRegistry(handlers=[handler])
        
        step = DummyStep(id="test-step", name="Test Step")
        retrieved_handler = registry.get_handler(step)
        
        # Call the handler
        from domain.run import RunContext
        from application.services.execution_deps import ExecutionDeps
        
        # Create minimal mocks
        class MockSecretProvider:
            def get(self):
                return {}
        
        class MockUrlResolver:
            def resolve_url(self, url):
                return url
        
        class MockLogger:
            def info(self, *args, **kwargs):
                pass
            def bind(self, **kwargs):
                return self
        
        ctx = RunContext()
        deps = ExecutionDeps(
            secret_provider=MockSecretProvider(),
            url_resolver=MockUrlResolver(),
            logger=MockLogger()
        )
        
        outcome = retrieved_handler.handle(step, ctx, deps)
        
        assert outcome.ok is True
        assert handler.call_count == 1
