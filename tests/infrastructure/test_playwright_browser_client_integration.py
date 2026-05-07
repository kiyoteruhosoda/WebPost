from __future__ import annotations

import importlib.util

import pytest

from infrastructure.browser.playwright_browser_client import PlaywrightBrowserClient


pytestmark = pytest.mark.integration


@pytest.mark.skipif(importlib.util.find_spec("playwright") is None, reason="playwright not installed")
def test_playwright_browser_client_real_browser_flow(tmp_path) -> None:
    client = PlaywrightBrowserClient(headless=True, viewport_width=1280, viewport_height=720)
    try:
        client.goto("https://example.com")
        client.wait_for_load_state("domcontentloaded", timeout_ms=5000)
        title = client.text("h1")
        screenshot_path = tmp_path / "example.png"
        saved = client.screenshot(str(screenshot_path))

        assert "Example Domain" in title
        assert saved == str(screenshot_path)
        assert screenshot_path.exists()
    finally:
        client.close()
