# application/services/form_composer.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

from application.services.template_renderer import TemplateRenderer, RenderSources


@dataclass(frozen=True)
class FormComposeResult:
    form_list: List[Tuple[str, str]]
    merged_from: Optional[str] = None
    merged_count: int = 0


class FormComposer:
    """
    Compose final form_list for HTTP requests.

    - Renders templates in step-provided form_list (TemplateRenderer)
    - Optionally merges vars[merge_from_vars] (dict[str, Any]) into form_list
    - Deterministic override rule:
        merged vars first, then rendered form_list (so explicit form_list wins on duplicates)
    """

    def __init__(self, renderer: TemplateRenderer):
        self._renderer = renderer

    def compose(
        self,
        form_list: List[Tuple[str, str]],
        src: RenderSources,
        vars_dict: Dict[str, Any],
        merge_from_vars: Optional[str],
    ) -> FormComposeResult:
        rendered = self._renderer.render_form_list(form_list, src)

        if not merge_from_vars:
            return FormComposeResult(form_list=rendered)

        merge_obj = vars_dict.get(merge_from_vars)
        if merge_obj is None:
            # merge target missing is treated as "no merge" (scenario flexibility)
            return FormComposeResult(form_list=rendered, merged_from=merge_from_vars, merged_count=0)

        if not isinstance(merge_obj, dict):
            raise ValueError(f"vars['{merge_from_vars}'] must be dict, got: {type(merge_obj).__name__}")

        merged_pairs: List[Tuple[str, str]] = []
        for k, v in merge_obj.items():
            if k is None:
                continue
            merged_pairs.append((str(k), "" if v is None else str(v)))

        # merged first, then rendered => explicit form_list overrides on duplicates (last wins)
        final = merged_pairs + rendered
        return FormComposeResult(
            form_list=final,
            merged_from=merge_from_vars,
            merged_count=len(merged_pairs),
        )
