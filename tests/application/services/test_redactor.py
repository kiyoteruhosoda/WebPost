# tests/application/services/test_redactor.py
import pytest
from application.services.redactor import mask_value, mask_pairs, mask_dict


class TestMaskValue:
    def test_mask_password(self):
        assert mask_value("password", "secret123") == "********"

    def test_mask_passwd(self):
        assert mask_value("passwd", "mypass") == "********"

    def test_mask_pass(self):
        assert mask_value("pass", "12345") == "********"

    def test_mask_authorization(self):
        assert mask_value("authorization", "Bearer token123") == "********"

    def test_mask_cookie(self):
        assert mask_value("cookie", "session=abc123") == "********"

    def test_mask_set_cookie(self):
        assert mask_value("set-cookie", "session=xyz789") == "********"

    def test_mask_case_insensitive(self):
        assert mask_value("PASSWORD", "secret") == "********"
        assert mask_value("Authorization", "token") == "********"
        assert mask_value("COOKIE", "data") == "********"

    def test_no_mask_regular_key(self):
        assert mask_value("username", "john") == "john"
        assert mask_value("email", "john@example.com") == "john@example.com"

    def test_mask_none_value(self):
        assert mask_value("password", None) == None

    def test_no_mask_numeric_value(self):
        assert mask_value("count", 42) == 42


class TestMaskPairs:
    def test_mask_pairs_with_sensitive_data(self):
        pairs = [
            ("username", "john"),
            ("password", "secret123"),
            ("email", "john@example.com")
        ]
        result = mask_pairs(pairs)
        assert result == [
            ("username", "john"),
            ("password", "********"),
            ("email", "john@example.com")
        ]

    def test_mask_pairs_empty_list(self):
        result = mask_pairs([])
        assert result == []

    def test_mask_pairs_no_sensitive_data(self):
        pairs = [("name", "Alice"), ("age", "30")]
        result = mask_pairs(pairs)
        assert result == [("name", "Alice"), ("age", "30")]

    def test_mask_pairs_all_sensitive(self):
        pairs = [
            ("password", "pass1"),
            ("authorization", "token1")
        ]
        result = mask_pairs(pairs)
        assert result == [
            ("password", "********"),
            ("authorization", "********")
        ]


class TestMaskDict:
    def test_mask_dict_with_sensitive_data(self):
        data = {
            "username": "john",
            "password": "secret123",
            "email": "john@example.com"
        }
        result = mask_dict(data)
        assert result == {
            "username": "john",
            "password": "********",
            "email": "john@example.com"
        }

    def test_mask_dict_empty_dict(self):
        result = mask_dict({})
        assert result == {}

    def test_mask_dict_no_sensitive_data(self):
        data = {"name": "Alice", "age": 30}
        result = mask_dict(data)
        assert result == {"name": "Alice", "age": 30}

    def test_mask_dict_all_sensitive(self):
        data = {
            "password": "pass1",
            "authorization": "Bearer token",
            "cookie": "session=abc"
        }
        result = mask_dict(data)
        assert result == {
            "password": "********",
            "authorization": "********",
            "cookie": "********"
        }

    def test_mask_dict_case_insensitive_keys(self):
        data = {
            "Password": "secret",
            "AUTHORIZATION": "token"
        }
        result = mask_dict(data)
        assert result == {
            "Password": "********",
            "AUTHORIZATION": "********"
        }
