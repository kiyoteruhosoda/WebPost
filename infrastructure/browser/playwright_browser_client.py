from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


LOGGER = logging.getLogger(__name__)


class PlaywrightBrowserClient:
    def __init__(
        self,
        headless: bool = True,
        viewport_width: Optional[int] = None,
        viewport_height: Optional[int] = None,
        user_agent: Optional[str] = None,
        locale: Optional[str] = None,
        timezone_id: Optional[str] = None,
    ) -> None:
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)
        context_kwargs = {}
        if viewport_width and viewport_height:
            context_kwargs["viewport"] = {"width": viewport_width, "height": viewport_height}
        if user_agent:
            context_kwargs["user_agent"] = user_agent
        if locale:
            context_kwargs["locale"] = locale
        if timezone_id:
            context_kwargs["timezone_id"] = timezone_id
        self._context = self._browser.new_context(**context_kwargs)
        self._page = self._context.new_page()

    def goto(self, url: str, timeout_ms: Optional[int] = None) -> None:
        self._page.goto(url, timeout=timeout_ms)

    def click(self, selector: str, timeout_ms: Optional[int] = None) -> None:
        self._page.click(selector, timeout=timeout_ms)

    def fill(self, selector: str, value: str, timeout_ms: Optional[int] = None) -> None:
        self._page.fill(selector, value, timeout=timeout_ms)

    def select(self, selector: str, value: str, timeout_ms: Optional[int] = None) -> None:
        self._page.select_option(selector, value=value, timeout=timeout_ms)

    def wait_for_selector(self, selector: str, timeout_ms: Optional[int] = None) -> None:
        self._page.wait_for_selector(selector, timeout=timeout_ms)

    def wait_for_url(self, url: str, timeout_ms: Optional[int] = None) -> None:
        self._page.wait_for_url(url, timeout=timeout_ms)

    def wait_for_load_state(self, state: str = "load", timeout_ms: Optional[int] = None) -> None:
        self._page.wait_for_load_state(state=state, timeout=timeout_ms)

    def text(self, selector: str) -> str:
        value = self._page.text_content(selector)
        return value or ""

    def attr(self, selector: str, attr: str) -> str:
        locator = self._page.locator(selector).first
        value = locator.get_attribute(attr)
        return value or ""

    def screenshot(self, path: Optional[str] = None) -> str:
        output = Path(path or "tmp/browser/screenshot.png")
        output.parent.mkdir(parents=True, exist_ok=True)
        self._page.screenshot(path=str(output), full_page=True)
        return str(output)

    def close(self) -> None:
        context = getattr(self, "_context", None)
        browser = getattr(self, "_browser", None)
        playwright = getattr(self, "_playwright", None)

        self._context = None
        self._browser = None
        self._playwright = None

        try:
            if context is not None:
                context.close()
        except Exception as exc:
            LOGGER.warning("Failed to close browser context", exc_info=exc)

        try:
            if browser is not None:
                browser.close()
        except Exception as exc:
            LOGGER.warning("Failed to close browser instance", exc_info=exc)

        try:
            if playwright is not None:
                playwright.stop()
        except Exception as exc:
            LOGGER.warning("Failed to stop playwright runtime", exc_info=exc)
