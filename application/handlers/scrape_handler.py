# application/handlers/scrape_handler.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from application.handlers.base import StepHandler
from application.outcome import StepOutcome
from application.services.execution_deps import ExecutionDeps
from application.services.redactor import mask_dict
from domain.run import RunContext
from domain.steps.scrape import ScrapeStep


class ScrapeStepHandler(StepHandler):
    """
    Scrape step handler.

    Commands:
      - hidden_inputs:
          Extract all <input type="hidden" name="..."> value into dict and save to ctx.vars[save_as]
      - css:
          Extract elements by CSS selector and save:
            - text (default) OR attribute value (attr)
            - first only OR all (multiple=True)
      - label_next_td:
          Find a label text in table header/cell and extract the next <td> text

    Stores results into ctx.vars under step.save_as key.
    """

    def supports(self, step) -> bool:
        return isinstance(step, ScrapeStep)

    def handle(self, step: ScrapeStep, ctx: RunContext, deps: ExecutionDeps) -> StepOutcome:
        try:
            if not ctx.last or not ctx.last.text:
                return StepOutcome(ok=False, error_message="scrape requires ctx.last.text (no previous response)")

            html = ctx.last.text
            soup = BeautifulSoup(html, "lxml")

            cmd = (step.command or "").strip().lower()

            if cmd == "hidden_inputs":
                return self._handle_hidden_inputs(step, soup, ctx, deps)

            if cmd == "css":
                return self._handle_css(step, soup, ctx, deps)

            if cmd == "label_next_td":
                return self._handle_label_next_td(step, soup, ctx, deps)

            return StepOutcome(ok=False, error_message=f"unsupported scrape command: {step.command}")

        except Exception as e:
            deps.logger.error(
                "scrape.step_failed",
                step_id=getattr(step, "id", "unknown"),
                command=getattr(step, "command", None),
                error=str(e),
            )
            return StepOutcome(ok=False, error_message=str(e))

    # -------------------------
    # command handlers
    # -------------------------

    def _handle_hidden_inputs(self, step: ScrapeStep, soup: BeautifulSoup, ctx: RunContext, deps: ExecutionDeps) -> StepOutcome:
        hidden: Dict[str, str] = {}

        # input[type=hidden][name]
        for inp in soup.select("input[type=hidden][name]"):
            name = inp.get("name")
            if not name:
                continue
            val = inp.get("value", "")
            hidden[name] = val if val is not None else ""

        save_as = step.save_as
        if not save_as:
            return StepOutcome(ok=False, error_message="scrape.hidden_inputs requires save_as")

        # Store
        ctx.vars[save_as] = hidden

        # Log summary (avoid huge output)
        keys = list(hidden.keys())
        deps.logger.debug(
            "scrape.hidden_inputs",
            step_id=step.id,
            save_as=save_as,
            count=len(hidden),
            keys_preview=keys[:10],
        )

        return StepOutcome(ok=True)

    def _handle_label_next_td(
        self, step: ScrapeStep, soup: BeautifulSoup, ctx: RunContext, deps: ExecutionDeps
    ) -> StepOutcome:
        label = getattr(step, "label", None)
        if not label:
            return StepOutcome(ok=False, error_message="scrape.label_next_td requires label")

        save_as = step.save_as
        if not save_as:
            return StepOutcome(ok=False, error_message="scrape.label_next_td requires save_as")

        label_text = str(label).strip()
        label_node = soup.find(string=lambda text: text and text.strip() == label_text)
        if not label_node:
            return StepOutcome(ok=False, error_message=f"label not found: {label_text}")

        label_parent = label_node.parent
        candidate_td = None
        if label_parent and label_parent.name in ("th", "td", "label"):
            candidate_td = label_parent.find_next_sibling("td")
        if candidate_td is None:
            candidate_td = label_parent.find_next("td") if label_parent else None

        if candidate_td is None:
            return StepOutcome(ok=False, error_message=f"no td found for label: {label_text}")

        value = candidate_td.get_text(strip=True)
        ctx.vars[save_as] = value
        deps.logger.debug(
            "scrape.label_next_td",
            step_id=step.id,
            label=label_text,
            save_as=save_as,
            value_preview=value[:200],
        )

        return StepOutcome(ok=True)

    def _handle_css(self, step: ScrapeStep, soup: BeautifulSoup, ctx: RunContext, deps: ExecutionDeps) -> StepOutcome:
        selector = step.selector
        if not selector:
            return StepOutcome(ok=False, error_message="scrape.css requires selector")

        save_as = step.save_as
        if not save_as:
            return StepOutcome(ok=False, error_message="scrape.css requires save_as")

        attr: Optional[str] = getattr(step, "attr", None)
        multiple: bool = bool(getattr(step, "multiple", False))

        nodes = soup.select(selector)

        if not nodes:
            # empty is not necessarily error; depends on scenario
            ctx.vars[save_as] = [] if multiple else ""
            deps.logger.warning(
                "scrape.css.not_found",
                step_id=step.id,
                selector=selector,
                save_as=save_as,
            )
            return StepOutcome(ok=True)

        def extract(node) -> str:
            if attr:
                v = node.get(attr)
                return "" if v is None else str(v)
            return node.get_text(strip=True)

        if multiple:
            values: List[str] = [extract(n) for n in nodes]
            ctx.vars[save_as] = values
            deps.logger.debug(
                "scrape.css",
                step_id=step.id,
                selector=selector,
                save_as=save_as,
                multiple=True,
                count=len(values),
                values_preview=values[:5],
            )
        else:
            value = extract(nodes[0])
            ctx.vars[save_as] = value
            deps.logger.debug(
                "scrape.css",
                step_id=step.id,
                selector=selector,
                save_as=save_as,
                multiple=False,
                value=value[:200],
            )

        return StepOutcome(ok=True)
