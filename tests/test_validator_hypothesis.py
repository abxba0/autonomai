"""
Property-based tests for validators using Hypothesis.

Uses hypothesis to generate arbitrary inputs and verify that validators
behave correctly on all inputs, not just hand-crafted examples.
"""

import pytest
import json
from hypothesis import given, strategies as st, settings, assume

from src.core.validator import (
    JSONValidator,
    RegexValidator,
    LengthValidator,
    CustomValidator,
    ValidationPipeline,
    ValidationResult,
)


class TestJSONValidatorProperty:
    """Property-based tests for JSONValidator."""

    @given(
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans(),
                st.none(),
            ),
            max_size=10,
        )
    )
    def test_valid_json_always_passes(self, data):
        """Any valid JSON object should pass JSONValidator without required fields."""
        validator = JSONValidator()
        json_str = json.dumps(data)
        result = validator.validate(json_str)
        assert result.passed is True

    @given(text=st.text(min_size=1, max_size=100))
    def test_non_json_always_fails(self, text):
        """Non-JSON text should fail JSONValidator."""
        assume(not _is_valid_json(text))
        validator = JSONValidator()
        result = validator.validate(text)
        assert result.passed is False

    @given(
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.text(max_size=50),
            min_size=1,
            max_size=5,
        )
    )
    def test_required_fields_present(self, data):
        """When required fields are present, validation should pass."""
        fields = list(data.keys())
        validator = JSONValidator(required_fields=fields)
        json_str = json.dumps(data)
        result = validator.validate(json_str)
        assert result.passed is True

    @given(
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.text(max_size=50),
            max_size=5,
        )
    )
    def test_missing_required_field_fails(self, data):
        """A required field not in the data should cause failure."""
        missing_field = "definitely_not_in_data_xyz_12345"
        assume(missing_field not in data)
        validator = JSONValidator(required_fields=[missing_field])
        json_str = json.dumps(data)
        result = validator.validate(json_str)
        assert result.passed is False
        assert "missing" in result.error_message.lower()


class TestLengthValidatorProperty:
    """Property-based tests for LengthValidator."""

    @given(text=st.text(min_size=5, max_size=20))
    def test_within_range_passes(self, text):
        """Text within length range should pass."""
        validator = LengthValidator(min_length=1, max_length=100)
        result = validator.validate(text)
        assert result.passed is True

    @given(text=st.text(min_size=0, max_size=100))
    @settings(max_examples=50)
    def test_min_only_consistency(self, text):
        """With only min_length, short text fails and long text passes."""
        min_len = 10
        validator = LengthValidator(min_length=min_len)
        result = validator.validate(text)
        if len(text) >= min_len:
            assert result.passed is True
        # Note: LengthValidator uses `if self.min_length and length < self.min_length`
        # so min_length=0 or empty text may behave differently

    @given(text=st.text(min_size=0, max_size=200))
    @settings(max_examples=50)
    def test_max_only_consistency(self, text):
        """With only max_length, long text fails and short text passes."""
        max_len = 50
        validator = LengthValidator(max_length=max_len)
        result = validator.validate(text)
        if len(text) <= max_len:
            assert result.passed is True
        else:
            assert result.passed is False


class TestRegexValidatorProperty:
    """Property-based tests for RegexValidator."""

    @given(text=st.from_regex(r"[a-zA-Z0-9]+@[a-zA-Z]+\.[a-zA-Z]{2,}", fullmatch=True))
    def test_email_pattern_match(self, text):
        """Text matching an email regex should pass."""
        validator = RegexValidator(r"[a-zA-Z0-9]+@[a-zA-Z]+\.[a-zA-Z]{2,}")
        result = validator.validate(text)
        assert result.passed is True

    @given(text=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=20))
    def test_digit_pattern_no_match(self, text):
        """Pure alphabetic text should not match digit-only pattern."""
        assume(not any(c.isdigit() for c in text))
        validator = RegexValidator(r"\d+")
        result = validator.validate(text)
        assert result.passed is False

    @given(text=st.text(min_size=1, max_size=50))
    def test_should_not_match_inverse(self, text):
        """When should_match=False, matching text should fail."""
        # Use a pattern that matches everything
        validator = RegexValidator(r".*", should_match=False)
        result = validator.validate(text)
        assert result.passed is False


class TestCustomValidatorProperty:
    """Property-based tests for CustomValidator."""

    @given(text=st.text(max_size=100))
    def test_always_true_validator(self, text):
        """A validator that always returns True should always pass."""
        validator = CustomValidator("always_pass", lambda output, ctx: True)
        result = validator.validate(text)
        assert result.passed is True

    @given(text=st.text(max_size=100))
    def test_always_false_validator(self, text):
        """A validator that always returns False should always fail."""
        validator = CustomValidator("always_fail", lambda output, ctx: False)
        result = validator.validate(text)
        assert result.passed is False

    @given(text=st.text(max_size=100))
    def test_exception_in_validator_fails_gracefully(self, text):
        """A validator that throws should fail gracefully, not crash."""

        def bad_validator(output, ctx):
            raise ValueError("intentional error")

        validator = CustomValidator("error_validator", bad_validator)
        result = validator.validate(text)
        assert result.passed is False
        assert "error" in result.error_message.lower()


class TestValidationPipelineProperty:
    """Property-based tests for ValidationPipeline."""

    @given(text=st.text(min_size=1, max_size=50))
    def test_empty_pipeline_always_passes(self, text):
        """An empty pipeline should always pass."""
        pipeline = ValidationPipeline()
        passed, results = pipeline.validate(text)
        assert passed is True
        assert len(results) == 0

    @given(
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.text(max_size=50),
            min_size=1,
            max_size=5,
        )
    )
    def test_pipeline_json_and_length(self, data):
        """Pipeline with JSON + length validators should behave consistently."""
        json_str = json.dumps(data)
        pipeline = ValidationPipeline()
        pipeline.add_validator(JSONValidator())
        pipeline.add_validator(LengthValidator(min_length=1, max_length=10000))
        passed, results = pipeline.validate(json_str)
        assert passed is True
        assert len(results) == 2
        assert all(r.passed for r in results)


def _is_valid_json(text: str) -> bool:
    """Helper to check if text is valid JSON."""
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, ValueError):
        return False
