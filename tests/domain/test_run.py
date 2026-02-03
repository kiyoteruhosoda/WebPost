# tests/domain/test_run.py
import pytest
from domain.run import LastResponse, RunContext


class TestLastResponse:
    def test_create_last_response(self):
        last_response = LastResponse(
            status=200,
            url="https://example.com",
            text="Hello World",
            headers={"Content-Type": "text/html"}
        )
        assert last_response.status == 200
        assert last_response.url == "https://example.com"
        assert last_response.text == "Hello World"
        assert last_response.headers == {"Content-Type": "text/html"}

    def test_last_response_empty_headers(self):
        last_response = LastResponse(
            status=404,
            url="https://example.com/notfound",
            text="Not Found",
            headers={}
        )
        assert last_response.status == 404
        assert last_response.headers == {}


class TestRunContext:
    def test_create_empty_run_context(self):
        ctx = RunContext()
        assert ctx.run_id == ""
        assert ctx.vars == {}
        assert ctx.state == {}
        assert ctx.last is None

    def test_create_run_context_with_run_id(self):
        ctx = RunContext(run_id="test-run-123")
        assert ctx.run_id == "test-run-123"

    def test_run_context_with_vars(self):
        ctx = RunContext(vars={"key1": "value1", "key2": 123})
        assert ctx.vars == {"key1": "value1", "key2": 123}

    def test_run_context_with_state(self):
        ctx = RunContext(state={"current_page": "login", "attempt": 1})
        assert ctx.state == {"current_page": "login", "attempt": 1}

    def test_run_context_with_last_response(self):
        last_response = LastResponse(
            status=200,
            url="https://example.com",
            text="Success",
            headers={"Content-Type": "application/json"}
        )
        ctx = RunContext(last=last_response)
        assert ctx.last == last_response
        assert ctx.last.status == 200

    def test_run_context_mutable_vars(self):
        ctx = RunContext()
        ctx.vars["new_key"] = "new_value"
        assert ctx.vars["new_key"] == "new_value"

    def test_run_context_mutable_state(self):
        ctx = RunContext()
        ctx.state["counter"] = 0
        ctx.state["counter"] += 1
        assert ctx.state["counter"] == 1

    def test_run_context_full_initialization(self):
        last_response = LastResponse(
            status=201,
            url="https://api.example.com/users",
            text='{"id": 1}',
            headers={"Content-Type": "application/json"}
        )
        ctx = RunContext(
            run_id="full-run-456",
            vars={"username": "testuser"},
            state={"step": 3},
            last=last_response
        )
        assert ctx.run_id == "full-run-456"
        assert ctx.vars["username"] == "testuser"
        assert ctx.state["step"] == 3
        assert ctx.last.status == 201
