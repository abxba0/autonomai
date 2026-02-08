"""
Unit tests for SecurityValidator (src/security/validation.py).

Tests input sanitization, SQL injection detection, XSS prevention,
command injection detection, URL/email validation, JSON depth limits,
and dictionary sanitization.
"""

import pytest

from src.security.validation import (
    SecurityValidator,
    sanitize_input,
    validate_input,
    RateLimitConfig,
    SecurityConfig,
)


class TestSanitizeInput:
    """Tests for SecurityValidator.sanitize_input."""

    def test_sanitize_empty_string(self):
        assert SecurityValidator.sanitize_input("") == ""

    def test_sanitize_none(self):
        assert SecurityValidator.sanitize_input(None) == ""

    def test_sanitize_plain_text(self):
        result = SecurityValidator.sanitize_input("Hello, world!")
        assert "Hello" in result
        assert "world" in result

    def test_sanitize_removes_null_bytes(self):
        result = SecurityValidator.sanitize_input("hello\x00world")
        assert "\x00" not in result

    def test_sanitize_strips_whitespace(self):
        result = SecurityValidator.sanitize_input("  hello  ")
        assert result == "hello"

    def test_sanitize_escapes_html(self):
        result = SecurityValidator.sanitize_input("<script>alert('xss')</script>")
        assert "<script>" not in result

    def test_sanitize_with_allowed_tags(self):
        result = SecurityValidator.sanitize_input(
            "<b>bold</b><script>bad</script>", allowed_tags=["b"]
        )
        assert "<b>" in result
        assert "<script>" not in result

    def test_convenience_function(self):
        result = sanitize_input("<b>test</b>")
        assert "<b>" not in result or "&lt;b&gt;" in result


class TestValidateInput:
    """Tests for SecurityValidator.validate_input."""

    def test_validate_empty_string(self):
        assert SecurityValidator.validate_input("") is True

    def test_validate_safe_general_input(self):
        assert SecurityValidator.validate_input("Hello, how are you?") is True

    def test_validate_convenience_function(self):
        assert validate_input("safe text") is True


class TestSQLInjection:
    """Tests for SQL injection detection."""

    @pytest.mark.parametrize(
        "payload",
        [
            "1' OR 1=1 --",
            "'; DROP TABLE users; --",
            "UNION SELECT * FROM passwords",
            "1; DELETE FROM users",
            "admin'--",
            "' OR 1=1",
        ],
    )
    def test_detect_sql_injection(self, payload):
        assert SecurityValidator.validate_input(payload, "sql") is False

    def test_safe_sql_input(self):
        assert SecurityValidator.validate_input("normal query text", "sql") is True


class TestXSSPrevention:
    """Tests for XSS detection."""

    @pytest.mark.parametrize(
        "payload",
        [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img onerror=alert(1)>",
            "data:text/html,<script>alert(1)</script>",
        ],
    )
    def test_detect_xss(self, payload):
        assert SecurityValidator.validate_input(payload, "xss") is False

    def test_safe_xss_input(self):
        assert SecurityValidator.validate_input("normal text content", "xss") is True


class TestCommandInjection:
    """Tests for command injection detection."""

    @pytest.mark.parametrize(
        "payload",
        [
            "; rm -rf /",
            "| cat /etc/passwd",
            "`whoami`",
            "${PATH}",
            "$(id)",
            "&& cat /etc/shadow",
        ],
    )
    def test_detect_command_injection(self, payload):
        assert SecurityValidator.validate_input(payload, "command") is False

    def test_safe_command_input(self):
        assert SecurityValidator.validate_input("normal text", "command") is True


class TestURLValidation:
    """Tests for URL validation."""

    def test_valid_https_url(self):
        assert SecurityValidator.validate_input("https://example.com", "url") is True

    def test_valid_http_url(self):
        assert SecurityValidator.validate_input("http://example.com/path", "url") is True

    def test_invalid_url_no_scheme(self):
        assert SecurityValidator.validate_input("not-a-url", "url") is False

    def test_invalid_url_no_netloc(self):
        assert SecurityValidator.validate_input("file:///etc/passwd", "url") is False


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        assert SecurityValidator.validate_input("user@example.com", "email") is True

    def test_invalid_email_no_at(self):
        assert SecurityValidator.validate_input("userexample.com", "email") is False

    def test_invalid_email_no_domain(self):
        assert SecurityValidator.validate_input("user@", "email") is False


class TestJSONValidation:
    """Tests for JSON validation with depth and size limits."""

    def test_valid_json(self):
        assert SecurityValidator.validate_json('{"key": "value"}') is True

    def test_invalid_json(self):
        assert SecurityValidator.validate_json("not json") is False

    def test_json_exceeds_max_size(self):
        large = '{"a": "' + "x" * 100 + '"}'
        assert SecurityValidator.validate_json(large, max_size=10) is False

    def test_json_exceeds_max_depth(self):
        # Build deeply nested JSON
        nested = '{"a": ' * 15 + '"deep"' + '}' * 15
        assert SecurityValidator.validate_json(nested, max_depth=5) is False

    def test_json_within_depth_limit(self):
        simple = '{"a": {"b": "c"}}'
        assert SecurityValidator.validate_json(simple, max_depth=5) is True

    def test_json_with_array(self):
        assert SecurityValidator.validate_json('[1, 2, 3]') is True


class TestDictSanitization:
    """Tests for dictionary sanitization."""

    def test_sanitize_empty_dict(self):
        assert SecurityValidator.sanitize_dict({}) == {}

    def test_sanitize_none_dict(self):
        assert SecurityValidator.sanitize_dict(None) == {}

    def test_sanitize_string_values(self):
        result = SecurityValidator.sanitize_dict({"key": "<script>bad</script>"})
        assert "<script>" not in result["key"]

    def test_sanitize_nested_dict(self):
        result = SecurityValidator.sanitize_dict({"outer": {"inner": "<b>test</b>"}})
        assert isinstance(result["outer"], dict)

    def test_sanitize_list_values(self):
        result = SecurityValidator.sanitize_dict(
            {"items": ["<script>x</script>", "safe"]}
        )
        assert "<script>" not in result["items"][0]

    def test_sanitize_non_string_values(self):
        result = SecurityValidator.sanitize_dict({"count": 42, "flag": True})
        assert result["count"] == 42
        assert result["flag"] is True

    def test_sanitize_with_allowed_keys(self):
        result = SecurityValidator.sanitize_dict(
            {"allowed": "value", "forbidden": "secret"},
            allowed_keys=["allowed"],
        )
        assert "allowed" in result
        assert "forbidden" not in result


class TestConfigModels:
    """Tests for configuration Pydantic models."""

    def test_rate_limit_config_defaults(self):
        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000

    def test_security_config_defaults(self):
        config = SecurityConfig()
        assert config.enable_authentication is True
        assert config.enable_rate_limiting is True
        assert config.enable_input_validation is True

    def test_general_validation_catches_attacks(self):
        assert SecurityValidator.validate_input("'; DROP TABLE users;--", "general") is False
        assert SecurityValidator.validate_input("<script>alert(1)</script>", "general") is False
        assert SecurityValidator.validate_input("; rm -rf /", "general") is False
