# tests/application/executor/test_step_executor.py
import pytest
from application.executor.step_executor import StepExecutor, ExecutionResult
from application.executor.handler_registry import HandlerRegistry
from application.handlers.base import StepHandler
from application.outcome import StepOutcome
from domain.steps.base import Step
from domain.run import RunContext


class DummyTestStep(Step):
    """A dummy test step for testing"""
    pass


class SuccessHandler(StepHandler):
    def __init__(self):
        self.handled_steps = []
        
    def supports(self, step: Step) -> bool:
        return isinstance(step, DummyTestStep)
    
    def handle(self, step, ctx, deps):
        self.handled_steps.append(step.id)
        return StepOutcome(ok=True)


class FailureHandler(StepHandler):
    def __init__(self):
        self.handled_steps = []
        
    def supports(self, step: Step) -> bool:
        return isinstance(step, DummyTestStep)
    
    def handle(self, step, ctx, deps):
        self.handled_steps.append(step.id)
        return StepOutcome(ok=False, error_message="Test failure")


class MockSecretProvider:
    def get(self):
        return {"api_key": "secret123"}


class MockUrlResolver:
    def resolve_url(self, url):
        return f"https://base.url{url}"


class MockLogger:
    def __init__(self):
        self.logs = []
        
    def info(self, message, **kwargs):
        self.logs.append({"message": message, **kwargs})
    
    def bind(self, **kwargs):
        # Return a new logger with bound context
        new_logger = MockLogger()
        new_logger.logs = self.logs
        return new_logger


class TestStepExecutor:
    def create_deps(self, logger=None):
        from application.services.execution_deps import ExecutionDeps
        if logger is None:
            logger = MockLogger()
        return ExecutionDeps(
            secret_provider=MockSecretProvider(),
            url_resolver=MockUrlResolver(),
            logger=logger
        )

    def test_execute_single_step_success(self):
        handler = SuccessHandler()
        registry = HandlerRegistry(handlers=[handler])
        executor = StepExecutor(registry=registry)
        
        steps = [DummyTestStep(id="step1", name="Step 1")]
        ctx = RunContext()
        deps = self.create_deps()
        
        result = executor.execute(steps, ctx, deps)
        
        assert result.ok is True
        assert result.failed_step_id is None
        assert result.error_message is None
        assert len(handler.handled_steps) == 1
        assert "step1" in handler.handled_steps

    def test_execute_multiple_steps_success(self):
        handler = SuccessHandler()
        registry = HandlerRegistry(handlers=[handler])
        executor = StepExecutor(registry=registry)
        
        steps = [
            DummyTestStep(id="step1", name="Step 1"),
            DummyTestStep(id="step2", name="Step 2"),
            DummyTestStep(id="step3", name="Step 3")
        ]
        ctx = RunContext()
        deps = self.create_deps()
        
        result = executor.execute(steps, ctx, deps)
        
        assert result.ok is True
        assert len(handler.handled_steps) == 3
        assert handler.handled_steps == ["step1", "step2", "step3"]

    def test_execute_step_failure(self):
        handler = FailureHandler()
        registry = HandlerRegistry(handlers=[handler])
        executor = StepExecutor(registry=registry)
        
        steps = [DummyTestStep(id="failing-step", name="Failing Step")]
        ctx = RunContext()
        deps = self.create_deps()
        
        result = executor.execute(steps, ctx, deps)
        
        assert result.ok is False
        assert result.failed_step_id == "failing-step"
        assert result.error_message == "Test failure"

    def test_execute_stops_on_first_failure(self):
        handler = FailureHandler()
        registry = HandlerRegistry(handlers=[handler])
        executor = StepExecutor(registry=registry)
        
        steps = [
            DummyTestStep(id="step1", name="Step 1"),
            DummyTestStep(id="step2", name="Step 2"),
            DummyTestStep(id="step3", name="Step 3")
        ]
        ctx = RunContext()
        deps = self.create_deps()
        
        result = executor.execute(steps, ctx, deps)
        
        # Should stop at first failure
        assert result.ok is False
        assert result.failed_step_id == "step1"
        assert len(handler.handled_steps) == 1

    def test_execute_skips_disabled_steps(self):
        handler = SuccessHandler()
        registry = HandlerRegistry(handlers=[handler])
        executor = StepExecutor(registry=registry)
        
        steps = [
            DummyTestStep(id="step1", name="Step 1", enabled=True),
            DummyTestStep(id="step2", name="Step 2", enabled=False),
            DummyTestStep(id="step3", name="Step 3", enabled=True)
        ]
        ctx = RunContext()
        deps = self.create_deps()
        
        result = executor.execute(steps, ctx, deps)
        
        assert result.ok is True
        assert len(handler.handled_steps) == 2
        assert "step1" in handler.handled_steps
        assert "step2" not in handler.handled_steps
        assert "step3" in handler.handled_steps

    def test_execute_empty_steps_list(self):
        handler = SuccessHandler()
        registry = HandlerRegistry(handlers=[handler])
        executor = StepExecutor(registry=registry)
        
        ctx = RunContext()
        deps = self.create_deps()
        
        result = executor.execute([], ctx, deps)
        
        assert result.ok is True
        assert len(handler.handled_steps) == 0

    def test_execute_generates_run_id_if_not_set(self):
        handler = SuccessHandler()
        registry = HandlerRegistry(handlers=[handler])
        executor = StepExecutor(registry=registry)
        
        steps = [DummyTestStep(id="step1", name="Step 1")]
        ctx = RunContext()  # No run_id set
        deps = self.create_deps()
        
        result = executor.execute(steps, ctx, deps)
        
        assert result.ok is True
        assert ctx.run_id != ""
        assert len(ctx.run_id) > 0

    def test_execute_preserves_existing_run_id(self):
        handler = SuccessHandler()
        registry = HandlerRegistry(handlers=[handler])
        executor = StepExecutor(registry=registry)
        
        steps = [DummyTestStep(id="step1", name="Step 1")]
        ctx = RunContext(run_id="existing-run-id")
        deps = self.create_deps()
        
        result = executor.execute(steps, ctx, deps)
        
        assert result.ok is True
        assert ctx.run_id == "existing-run-id"

    def test_execute_logs_step_start_and_end(self):
        handler = SuccessHandler()
        registry = HandlerRegistry(handlers=[handler])
        executor = StepExecutor(registry=registry)
        
        steps = [DummyTestStep(id="step1", name="Step 1")]
        ctx = RunContext()
        logger = MockLogger()
        deps = self.create_deps(logger=logger)
        
        result = executor.execute(steps, ctx, deps)
        
        assert result.ok is True
        # Check that logs were created
        log_messages = [log["message"] for log in logger.logs]
        assert "step.start" in log_messages
        assert "step.end" in log_messages

    def test_execute_handler_returns_none_raises_error(self):
        class NoneHandler(StepHandler):
            def supports(self, step: Step) -> bool:
                return isinstance(step, DummyTestStep)
            
            def handle(self, step, ctx, deps):
                return None  # Invalid: should return StepOutcome
        
        handler = NoneHandler()
        registry = HandlerRegistry(handlers=[handler])
        executor = StepExecutor(registry=registry)
        
        steps = [DummyTestStep(id="step1", name="Step 1")]
        ctx = RunContext()
        deps = self.create_deps()
        
        with pytest.raises(RuntimeError, match="Handler returned None"):
            executor.execute(steps, ctx, deps)


class TestExecutionResult:
    def test_create_success_result(self):
        result = ExecutionResult(ok=True)
        assert result.ok is True
        assert result.failed_step_id is None
        assert result.error_message is None

    def test_create_failure_result(self):
        result = ExecutionResult(
            ok=False,
            failed_step_id="step-5",
            error_message="Connection timeout"
        )
        assert result.ok is False
        assert result.failed_step_id == "step-5"
        assert result.error_message == "Connection timeout"

    def test_result_frozen(self):
        result = ExecutionResult(ok=True)
        with pytest.raises(Exception):  # FrozenInstanceError
            result.ok = False
