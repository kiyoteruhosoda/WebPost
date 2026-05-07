from __future__ import annotations

from pathlib import Path
from typing import Optional

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright


class PlaywrightBrowserClient:
    def __init__(self, headless: bool = True) -> None:
        self._playwright = sync_playwright().start()
        self._browser: Browser = self._playwright.chromium.launch(headless=headless)
        self._context: BrowserContext = self._browser.new_context()
        self._page: Page = self._context.new_page()

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
        self._context.close()
        self._browser.close()
        self._playwright.stop()
