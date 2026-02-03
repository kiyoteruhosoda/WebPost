# tests/application/test_http_trace.py
import pytest
from application.http_trace import CookieSnapshot, HttpResponseMeta, HttpTrace


class TestCookieSnapshot:
    def test_create_empty_cookie_snapshot(self):
        snapshot = CookieSnapshot(items=[])
        assert snapshot.items == []

    def test_create_cookie_snapshot_with_items(self):
        cookies = [
            {"name": "session_id", "value": "abc123", "domain": "example.com"},
            {"name": "user", "value": "john", "domain": "example.com"}
        ]
        snapshot = CookieSnapshot(items=cookies)
        assert len(snapshot.items) == 2
        assert snapshot.items[0]["name"] == "session_id"

    def test_cookie_snapshot_frozen(self):
        snapshot = CookieSnapshot(items=[])
        with pytest.raises(Exception):  # FrozenInstanceError
            snapshot.items = [{"name": "test"}]


class TestHttpResponseMeta:
    def test_create_http_response_meta(self):
        meta = HttpResponseMeta(
            status=200,
            url="https://example.com",
            headers={"Content-Type": "text/html"},
            encoding="utf-8",
            content_type="text/html",
            history=[],
            body_len=1024,
            body_sha256="abcdef123456"
        )
        assert meta.status == 200
        assert meta.url == "https://example.com"
        assert meta.encoding == "utf-8"
        assert meta.body_len == 1024

    def test_create_http_response_meta_with_history(self):
        history = [
            {"status": 301, "url": "https://old.example.com"},
            {"status": 302, "url": "https://redirect.example.com"}
        ]
        meta = HttpResponseMeta(
            status=200,
            url="https://example.com",
            headers={},
            encoding=None,
            content_type=None,
            history=history,
            body_len=512,
            body_sha256="xyz789"
        )
        assert len(meta.history) == 2
        assert meta.history[0]["status"] == 301

    def test_http_response_meta_frozen(self):
        meta = HttpResponseMeta(
            status=200,
            url="https://example.com",
            headers={},
            encoding=None,
            content_type=None,
            history=[],
            body_len=0,
            body_sha256=""
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            meta.status = 404


class TestHttpTrace:
    def test_create_minimal_http_trace(self):
        trace = HttpTrace(
            run_id="run-123",
            step_id="step-1",
            method="GET",
            url="https://example.com"
        )
        assert trace.run_id == "run-123"
        assert trace.step_id == "step-1"
        assert trace.method == "GET"
        assert trace.url == "https://example.com"
        assert trace.allow_redirects is None
        assert trace.text_head == ""
        assert trace.html_title is None

    def test_create_http_trace_with_headers(self):
        trace = HttpTrace(
            run_id="run-456",
            step_id="step-2",
            method="POST",
            url="https://api.example.com",
            request_headers={"Authorization": "Bearer token123"}
        )
        assert trace.request_headers == {"Authorization": "Bearer token123"}

    def test_create_http_trace_with_form(self):
        form_data = [("username", "testuser"), ("password", "secret")]
        trace = HttpTrace(
            run_id="run-789",
            step_id="step-3",
            method="POST",
            url="https://example.com/login",
            request_form=form_data
        )
        assert trace.request_form == form_data
        assert len(trace.request_form) == 2

    def test_create_http_trace_with_cookies(self):
        cookies_before = CookieSnapshot(items=[{"name": "session", "value": "old"}])
        cookies_after = CookieSnapshot(items=[{"name": "session", "value": "new"}])
        trace = HttpTrace(
            run_id="run-999",
            step_id="step-4",
            method="GET",
            url="https://example.com",
            cookies_before=cookies_before,
            cookies_after=cookies_after
        )
        assert trace.cookies_before.items[0]["value"] == "old"
        assert trace.cookies_after.items[0]["value"] == "new"

    def test_create_http_trace_with_response(self):
        response = HttpResponseMeta(
            status=201,
            url="https://api.example.com/users",
            headers={"Content-Type": "application/json"},
            encoding="utf-8",
            content_type="application/json",
            history=[],
            body_len=256,
            body_sha256="hash123"
        )
        trace = HttpTrace(
            run_id="run-111",
            step_id="step-5",
            method="POST",
            url="https://api.example.com/users",
            response=response,
            text_head='{"id": 1}',
            html_title=None,
            full_text='{"id": 1, "name": "test"}'
        )
        assert trace.response.status == 201
        assert trace.text_head == '{"id": 1}'
        assert trace.full_text == '{"id": 1, "name": "test"}'

    def test_create_http_trace_with_merge_info(self):
        trace = HttpTrace(
            run_id="run-222",
            step_id="step-6",
            method="POST",
            url="https://example.com",
            merged_from="form_vars",
            merged_count=5,
            collision_keys=["key1", "key2"]
        )
        assert trace.merged_from == "form_vars"
        assert trace.merged_count == 5
        assert trace.collision_keys == ["key1", "key2"]

    def test_create_http_trace_with_raw_bytes(self):
        raw_data = b"Binary data"
        trace = HttpTrace(
            run_id="run-333",
            step_id="step-7",
            method="GET",
            url="https://example.com/image.png",
            raw_bytes=raw_data
        )
        assert trace.raw_bytes == raw_data

    def test_http_trace_frozen(self):
        trace = HttpTrace(
            run_id="run-444",
            step_id="step-8",
            method="GET",
            url="https://example.com"
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            trace.method = "POST"
