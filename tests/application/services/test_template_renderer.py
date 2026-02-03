# tests/application/services/test_template_renderer.py
import pytest
from application.services.template_renderer import (
    TemplateRenderer,
    TemplateRenderError,
    RenderSources
)


class TestTemplateRenderer:
    def test_render_simple_vars(self):
        renderer = TemplateRenderer()
        src = RenderSources(
            vars={"name": "Alice"},
            state={},
            secrets={},
            last={}
        )
        result = renderer._render_str("Hello ${vars.name}", src)
        assert result == "Hello Alice"

    def test_render_state_variable(self):
        renderer = TemplateRenderer()
        src = RenderSources(
            vars={},
            state={"counter": 5},
            secrets={},
            last={}
        )
        result = renderer._render_str("Count: ${state.counter}", src)
        assert result == "Count: 5"

    def test_render_secrets_variable(self):
        renderer = TemplateRenderer()
        src = RenderSources(
            vars={},
            state={},
            secrets={"api_key": "secret123"},
            last={}
        )
        result = renderer._render_str("Key: ${secrets.api_key}", src)
        assert result == "Key: secret123"

    def test_render_last_variable(self):
        renderer = TemplateRenderer()
        src = RenderSources(
            vars={},
            state={},
            secrets={},
            last={"status": 200, "url": "https://example.com"}
        )
        result = renderer._render_str("Status: ${last.status}", src)
        assert result == "Status: 200"

    def test_render_nested_object(self):
        renderer = TemplateRenderer()
        src = RenderSources(
            vars={"user": {"name": "Bob", "age": 30}},
            state={},
            secrets={},
            last={}
        )
        result = renderer._render_str("${vars.user.name}", src)
        assert result == "Bob"

    def test_render_multiple_templates(self):
        renderer = TemplateRenderer()
        src = RenderSources(
            vars={"first": "John", "last": "Doe"},
            state={},
            secrets={},
            last={}
        )
        result = renderer._render_str("${vars.first} ${vars.last}", src)
        assert result == "John Doe"

    def test_render_no_template(self):
        renderer = TemplateRenderer()
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        result = renderer._render_str("Plain text", src)
        assert result == "Plain text"

    def test_render_none_value(self):
        renderer = TemplateRenderer()
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        result = renderer._render_str(None, src)
        assert result == ""

    def test_render_list_expansion(self):
        renderer = TemplateRenderer()
        src = RenderSources(
            vars={"items": [{"id": 1}, {"id": 2}, {"id": 3}]},
            state={},
            secrets={},
            last={}
        )
        result = renderer._render_str("${vars.items[*]}", src)
        # List is joined to string
        assert "id" in result or result != ""

    def test_render_list_index(self):
        renderer = TemplateRenderer()
        src = RenderSources(
            vars={"items": ["apple", "banana", "cherry"]},
            state={},
            secrets={},
            last={}
        )
        result = renderer._render_str("${vars.items.1}", src)
        assert result == "banana"

    def test_render_missing_key_returns_empty(self):
        renderer = TemplateRenderer()
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        result = renderer._render_str("${vars.missing}", src)
        assert result == ""

    def test_render_unclosed_template_raises_error(self):
        renderer = TemplateRenderer()
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        with pytest.raises(TemplateRenderError, match="unclosed template"):
            renderer._render_str("${vars.name", src)

    def test_render_unknown_root_raises_error(self):
        renderer = TemplateRenderer()
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        with pytest.raises(TemplateRenderError, match="unknown root"):
            renderer._render_str("${unknown.key}", src)

    def test_render_form_list(self):
        renderer = TemplateRenderer()
        src = RenderSources(
            vars={"username": "alice", "password": "secret"},
            state={},
            secrets={},
            last={}
        )
        form_list = [
            ("user", "${vars.username}"),
            ("pass", "${vars.password}"),
            ("static", "value")
        ]
        result = renderer.render_form_list(form_list, src)
        assert result == [
            ("user", "alice"),
            ("pass", "secret"),
            ("static", "value")
        ]

    def test_render_form_list_empty(self):
        renderer = TemplateRenderer()
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        result = renderer.render_form_list([], src)
        assert result == []

    def test_split_root(self):
        renderer = TemplateRenderer()
        assert renderer._split_root("vars.name") == ("vars", "name")
        assert renderer._split_root("state.counter.value") == ("state", "counter.value")
        assert renderer._split_root("vars") == ("vars", "")

    def test_resolve_path_simple(self):
        renderer = TemplateRenderer()
        obj = {"name": "Alice", "age": 30}
        result = renderer._resolve_path(obj, "name")
        assert result == "Alice"

    def test_resolve_path_nested(self):
        renderer = TemplateRenderer()
        obj = {"user": {"profile": {"name": "Bob"}}}
        result = renderer._resolve_path(obj, "user.profile.name")
        assert result == "Bob"

    def test_resolve_path_list_index(self):
        renderer = TemplateRenderer()
        obj = {"items": ["first", "second", "third"]}
        result = renderer._resolve_path(obj, "items.0")
        assert result == "first"

    def test_resolve_path_out_of_bounds_index(self):
        renderer = TemplateRenderer()
        obj = {"items": ["first", "second"]}
        result = renderer._resolve_path(obj, "items.10")
        assert result == ""

    def test_resolve_path_list_expansion(self):
        renderer = TemplateRenderer()
        obj = {"items": [1, 2, 3]}
        result = renderer._resolve_path(obj, "items[*]")
        assert result == [1, 2, 3]

    def test_resolve_path_invalid_list_expansion_raises_error(self):
        renderer = TemplateRenderer()
        obj = {"value": "not_a_list"}
        with pytest.raises(TemplateRenderError, match="is not list"):
            renderer._resolve_path(obj, "value[*]")
