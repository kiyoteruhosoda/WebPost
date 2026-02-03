# tests/mock_http_client.py
"""
Mock HTTP client for testing scenarios without external dependencies.
Returns predefined HTML responses based on URL patterns.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple, Optional

from application.ports.http_client import HttpClientPort, HttpResponse


class MockHttpClient(HttpClientPort):
    """
    Mock HTTP client that returns predefined responses.
    
    URL mapping:
    - /FRPC010G_LoginAction.do (GET) -> login_page.html
    - /FRPC010G_LoginAction.do (POST) -> login_success.html
    - /FRPC0400G_RegAction.do (POST) -> reservation_success.html
    """

    def __init__(self):
        self._fixtures_dir = Path(__file__).parent / "fixtures"
        self._cookies: Dict[str, str] = {}

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        form_list: Optional[List[Tuple[str, str]]] = None,
        allow_redirects: Optional[bool] = None,
    ) -> HttpResponse:
        """Execute HTTP request (generic method)"""
        if method.upper() == "GET":
            return self.get(url, headers)
        elif method.upper() == "POST":
            return self.post(url, form_list or [], headers)
        else:
            return HttpResponse(
                status=405,
                url=url,
                text="Method Not Allowed",
                headers={"Content-Type": "text/html"},
            )

    def snapshot_cookies(self) -> Dict[str, str]:
        """Return current cookies snapshot"""
        return self._cookies.copy()

    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> HttpResponse:
        """Execute GET request"""
        if "FRPC010G_LoginAction" in url:
            html = self._load_fixture("login_page.html")
            return HttpResponse(
                status=200,
                url=url,
                text=html,
                headers={"Content-Type": "text/html; charset=UTF-8"},
            )
        
        # Default 404
        return HttpResponse(
            status=404,
            url=url,
            text="Not Found",
            headers={"Content-Type": "text/html"},
            raw_bytes=b"Not Found",
        )

    def post(
        self,
        url: str,
        form_data: List[Tuple[str, str]],
        headers: Optional[Dict[str, str]] = None,
    ) -> HttpResponse:
        """Execute POST request"""
        # Convert form_data to dict for inspection (last value wins for duplicate keys)
        form_dict = {}
        for key, value in form_data:
            if key not in form_dict:
                form_dict[key] = []
            form_dict[key].append(value)
        
        if "FRPC010G_LoginAction" in url:
            # Login POST
            html = self._load_fixture("login_success.html")
            self._cookies["JSESSIONID"] = "mock_session_123"
            return HttpResponse(
                status=200,
                url=url,
                text=html,
                headers={"Content-Type": "text/html; charset=UTF-8"},
            )
        
        if "FRPC0400G_RegAction" in url:
            # Reservation POST
            html = self._load_fixture("reservation_success.html")
            return HttpResponse(
                status=200,
                url=url,
                text=html,
                headers={"Content-Type": "text/html; charset=UTF-8"},
            )
        
        # Default 404
        return HttpResponse(
            status=404,
            url=url,
            text="Not Found",
            headers={"Content-Type": "text/html"},
        )

    def _load_fixture(self, filename: str) -> str:
        """Load HTML fixture file"""
        fixture_path = self._fixtures_dir / filename
        if not fixture_path.exists():
            return f"<html><body>Fixture not found: {filename}</body></html>"
        
        # Try UTF-8 first, then Shift_JIS
        for encoding in ("utf-8", "shift_jis", "cp932"):
            try:
                with fixture_path.open("r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        # Fallback
        return f"<html><body>Encoding error: {filename}</body></html>"
