# tests/domain/test_expr.py
import pytest
from domain.steps.expr import ExpressionEvaluator


class TestExpressionEvaluator:
    def test_resolve_simple_template(self):
        evaluator = ExpressionEvaluator()
        result = evaluator.resolve("Hello ${name}", {"name": "World"})
        assert result == "Hello World"

    def test_resolve_multiple_placeholders(self):
        evaluator = ExpressionEvaluator()
        result = evaluator.resolve(
            "${greeting} ${name}!",
            {"greeting": "Hello", "name": "Alice"}
        )
        assert result == "Hello Alice!"

    def test_resolve_no_placeholder(self):
        evaluator = ExpressionEvaluator()
        result = evaluator.resolve("Plain text", {"name": "World"})
        assert result == "Plain text"

    def test_resolve_missing_key(self):
        evaluator = ExpressionEvaluator()
        result = evaluator.resolve("Hello ${name}", {"other": "value"})
        assert result == "Hello ${name}"

    def test_resolve_numeric_value(self):
        evaluator = ExpressionEvaluator()
        result = evaluator.resolve("Count: ${count}", {"count": 42})
        assert result == "Count: 42"

    def test_matches_pattern_success(self):
        evaluator = ExpressionEvaluator()
        assert evaluator.matches("test123", r"test\d+") is True

    def test_matches_pattern_failure(self):
        evaluator = ExpressionEvaluator()
        assert evaluator.matches("test", r"\d+") is False

    def test_matches_empty_text(self):
        evaluator = ExpressionEvaluator()
        assert evaluator.matches("", r".*") is True

    def test_matches_none_text(self):
        evaluator = ExpressionEvaluator()
        assert evaluator.matches(None, r".*") is True

    def test_contains_found(self):
        evaluator = ExpressionEvaluator()
        assert evaluator.contains("hello world", "world") is True

    def test_contains_not_found(self):
        evaluator = ExpressionEvaluator()
        assert evaluator.contains("hello world", "foo") is False

    def test_contains_empty_substring(self):
        evaluator = ExpressionEvaluator()
        assert evaluator.contains("hello world", "") is True

    def test_contains_none_text(self):
        evaluator = ExpressionEvaluator()
        assert evaluator.contains(None, "world") is False

    def test_not_contains_success(self):
        evaluator = ExpressionEvaluator()
        assert evaluator.not_contains("hello world", "foo") is True

    def test_not_contains_failure(self):
        evaluator = ExpressionEvaluator()
        assert evaluator.not_contains("hello world", "world") is False

    def test_not_contains_empty_substring(self):
        evaluator = ExpressionEvaluator()
        assert evaluator.not_contains("hello world", "") is False

    def test_not_contains_none_text(self):
        evaluator = ExpressionEvaluator()
        assert evaluator.not_contains(None, "world") is True
