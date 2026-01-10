from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
import json
import re


@dataclass
class ValidationResult:
    """Result of a validation check"""

    passed: bool
    validator_name: str
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class BaseValidator(ABC):
    """Base class for all validators"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def validate(
        self, output: str, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate the model output"""
        pass


class JSONValidator(BaseValidator):
    """Validates JSON structure"""

    def __init__(self, required_fields: Optional[List[str]] = None):
        super().__init__("JSONValidator")
        self.required_fields = required_fields or []

    def validate(
        self, output: str, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        try:
            data = json.loads(output)

            # Check required fields
            missing_fields = [f for f in self.required_fields if f not in data]
            if missing_fields:
                return ValidationResult(
                    passed=False,
                    validator_name=self.name,
                    error_message=f"Missing required fields: {missing_fields}",
                    error_details={"missing_fields": missing_fields},
                )

            return ValidationResult(passed=True, validator_name=self.name)

        except json.JSONDecodeError as e:
            return ValidationResult(
                passed=False,
                validator_name=self.name,
                error_message=f"Invalid JSON: {str(e)}",
                error_details={"parse_error": str(e)},
            )


class RegexValidator(BaseValidator):
    """Validates output against regex pattern"""

    def __init__(self, pattern: str, should_match: bool = True):
        super().__init__("RegexValidator")
        self.pattern = re.compile(pattern)
        self.should_match = should_match

    def validate(
        self, output: str, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        matches = bool(self.pattern.search(output))

        if matches == self.should_match:
            return ValidationResult(passed=True, validator_name=self.name)

        return ValidationResult(
            passed=False,
            validator_name=self.name,
            error_message=f"Pattern {'not found' if self.should_match else 'found'}: {self.pattern.pattern}",
            error_details={
                "pattern": self.pattern.pattern,
                "should_match": self.should_match,
            },
        )


class LengthValidator(BaseValidator):
    """Validates output length"""

    def __init__(
        self, min_length: Optional[int] = None, max_length: Optional[int] = None
    ):
        super().__init__("LengthValidator")
        self.min_length = min_length
        self.max_length = max_length

    def validate(
        self, output: str, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        length = len(output)

        if self.min_length and length < self.min_length:
            return ValidationResult(
                passed=False,
                validator_name=self.name,
                error_message=f"Output too short: {length} < {self.min_length}",
                error_details={"actual": length, "min": self.min_length},
            )

        if self.max_length and length > self.max_length:
            return ValidationResult(
                passed=False,
                validator_name=self.name,
                error_message=f"Output too long: {length} > {self.max_length}",
                error_details={"actual": length, "max": self.max_length},
            )

        return ValidationResult(passed=True, validator_name=self.name)


class CustomValidator(BaseValidator):
    """Allows custom validation function"""

    def __init__(self, name: str, validation_fn):
        super().__init__(name)
        self.validation_fn = validation_fn

    def validate(
        self, output: str, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        try:
            result = self.validation_fn(output, context)
            if isinstance(result, bool):
                return ValidationResult(
                    passed=result,
                    validator_name=self.name,
                    error_message=None if result else "Custom validation failed",
                )
            return result
        except Exception as e:
            return ValidationResult(
                passed=False,
                validator_name=self.name,
                error_message=f"Validation error: {str(e)}",
                error_details={"exception": str(e)},
            )


class ValidationPipeline:
    """Manages multiple validators"""

    def __init__(self):
        self.validators: List[BaseValidator] = []

    def add_validator(self, validator: BaseValidator):
        """Add a validator to the pipeline"""
        self.validators.append(validator)

    def validate(
        self, output: str, context: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, List[ValidationResult]]:
        """Run all validators"""
        results = []
        all_passed = True

        for validator in self.validators:
            result = validator.validate(output, context)
            results.append(result)
            if not result.passed:
                all_passed = False

        return all_passed, results
