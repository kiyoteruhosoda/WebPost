from __future__ import annotations

import logging

from infrastructure.browser.playwright_browser_client import PlaywrightBrowserClient


class FailingClosable:
    def __init__(self, message: str) -> None:
        self._message = message

    def close(self) -> None:
        raise RuntimeError(self._message)


class FailingStoppable:
    def stop(self) -> None:
        raise RuntimeError("playwright-stop-failed")


def test_close_logs_warning_when_sub_resource_close_fails(caplog) -> None:
    client = PlaywrightBrowserClient.__new__(PlaywrightBrowserClient)
    client._context = FailingClosable("context-close-failed")
    client._browser = FailingClosable("browser-close-failed")
    client._playwright = FailingStoppable()

    with caplog.at_level(logging.WARNING):
        client.close()

    assert "Failed to close browser context" in caplog.text
    assert "Failed to close browser instance" in caplog.text
    assert "Failed to stop playwright runtime" in caplog.text
