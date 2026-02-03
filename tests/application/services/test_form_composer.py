# tests/application/services/test_form_composer.py
import pytest
from application.services.form_composer import FormComposer, FormComposeResult
from application.services.template_renderer import TemplateRenderer, RenderSources


class TestFormComposer:
    def test_compose_without_merge(self):
        renderer = TemplateRenderer()
        composer = FormComposer(renderer)
        
        form_list = [("key1", "value1"), ("key2", "value2")]
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        
        result = composer.compose(
            form_list=form_list,
            src=src,
            vars_dict={},
            merge_from_vars=None
        )
        
        assert result.form_list == [("key1", "value1"), ("key2", "value2")]
        assert result.merged_from is None
        assert result.merged_count == 0

    def test_compose_with_template_rendering(self):
        renderer = TemplateRenderer()
        composer = FormComposer(renderer)
        
        form_list = [("username", "${vars.user}"), ("email", "${vars.email}")]
        src = RenderSources(
            vars={"user": "alice", "email": "alice@example.com"},
            state={},
            secrets={},
            last={}
        )
        
        result = composer.compose(
            form_list=form_list,
            src=src,
            vars_dict=src.vars,
            merge_from_vars=None
        )
        
        assert result.form_list == [("username", "alice"), ("email", "alice@example.com")]

    def test_compose_with_merge_from_vars(self):
        renderer = TemplateRenderer()
        composer = FormComposer(renderer)
        
        form_list = [("key1", "value1")]
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        vars_dict = {
            "merge_data": {
                "key2": "value2",
                "key3": "value3"
            }
        }
        
        result = composer.compose(
            form_list=form_list,
            src=src,
            vars_dict=vars_dict,
            merge_from_vars="merge_data"
        )
        
        # merged first, then rendered form_list (so explicit form_list overrides)
        assert len(result.form_list) == 3
        assert ("key2", "value2") in result.form_list
        assert ("key3", "value3") in result.form_list
        assert ("key1", "value1") in result.form_list
        assert result.merged_from == "merge_data"
        assert result.merged_count == 2

    def test_compose_merge_override_behavior(self):
        renderer = TemplateRenderer()
        composer = FormComposer(renderer)
        
        form_list = [("key1", "explicit_value")]
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        vars_dict = {
            "merge_data": {
                "key1": "merged_value",
                "key2": "value2"
            }
        }
        
        result = composer.compose(
            form_list=form_list,
            src=src,
            vars_dict=vars_dict,
            merge_from_vars="merge_data"
        )
        
        # merged pairs come first, then explicit form_list
        # last wins on duplicate keys, so explicit value should appear last
        assert result.form_list == [
            ("key1", "merged_value"),
            ("key2", "value2"),
            ("key1", "explicit_value")
        ]

    def test_compose_merge_target_missing(self):
        renderer = TemplateRenderer()
        composer = FormComposer(renderer)
        
        form_list = [("key1", "value1")]
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        vars_dict = {}
        
        result = composer.compose(
            form_list=form_list,
            src=src,
            vars_dict=vars_dict,
            merge_from_vars="missing_key"
        )
        
        # Missing merge target is treated as "no merge"
        assert result.form_list == [("key1", "value1")]
        assert result.merged_from == "missing_key"
        assert result.merged_count == 0

    def test_compose_merge_non_dict_raises_error(self):
        renderer = TemplateRenderer()
        composer = FormComposer(renderer)
        
        form_list = [("key1", "value1")]
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        vars_dict = {"merge_data": "not_a_dict"}
        
        with pytest.raises(ValueError, match="must be dict"):
            composer.compose(
                form_list=form_list,
                src=src,
                vars_dict=vars_dict,
                merge_from_vars="merge_data"
            )

    def test_compose_merge_with_none_key(self):
        renderer = TemplateRenderer()
        composer = FormComposer(renderer)
        
        form_list = [("key1", "value1")]
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        vars_dict = {
            "merge_data": {
                None: "should_skip",
                "key2": "value2"
            }
        }
        
        result = composer.compose(
            form_list=form_list,
            src=src,
            vars_dict=vars_dict,
            merge_from_vars="merge_data"
        )
        
        # None keys are skipped
        assert ("key2", "value2") in result.form_list
        assert (None, "should_skip") not in result.form_list

    def test_compose_merge_with_none_value(self):
        renderer = TemplateRenderer()
        composer = FormComposer(renderer)
        
        form_list = []
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        vars_dict = {
            "merge_data": {
                "key1": None,
                "key2": "value2"
            }
        }
        
        result = composer.compose(
            form_list=form_list,
            src=src,
            vars_dict=vars_dict,
            merge_from_vars="merge_data"
        )
        
        # None values are converted to empty string
        assert ("key1", "") in result.form_list
        assert ("key2", "value2") in result.form_list

    def test_compose_merge_converts_to_string(self):
        renderer = TemplateRenderer()
        composer = FormComposer(renderer)
        
        form_list = []
        src = RenderSources(vars={}, state={}, secrets={}, last={})
        vars_dict = {
            "merge_data": {
                "number": 42,
                "boolean": True,
                "text": "hello"
            }
        }
        
        result = composer.compose(
            form_list=form_list,
            src=src,
            vars_dict=vars_dict,
            merge_from_vars="merge_data"
        )
        
        # All values should be converted to strings
        assert ("number", "42") in result.form_list
        assert ("boolean", "True") in result.form_list
        assert ("text", "hello") in result.form_list


class TestFormComposeResult:
    def test_create_result_without_merge(self):
        result = FormComposeResult(form_list=[("key", "value")])
        assert result.form_list == [("key", "value")]
        assert result.merged_from is None
        assert result.merged_count == 0

    def test_create_result_with_merge(self):
        result = FormComposeResult(
            form_list=[("key1", "value1"), ("key2", "value2")],
            merged_from="merge_vars",
            merged_count=2
        )
        assert len(result.form_list) == 2
        assert result.merged_from == "merge_vars"
        assert result.merged_count == 2

    def test_result_frozen(self):
        result = FormComposeResult(form_list=[])
        with pytest.raises(Exception):  # FrozenInstanceError
            result.merged_count = 5
