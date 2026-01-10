"""
Input validation and sanitization for security
"""

import re
import html
from typing import Any, Dict, List, Optional, Union, Callable
from urllib.parse import urlparse
import json
from pydantic import BaseModel, Field, validator
import bleach


class SecurityValidator:
    """Security validator for input sanitization and validation"""

    # Common attack patterns
    SQL_INJECTION_PATTERNS = [
        r"(?i)(union\s+select)",
        r"(?i)(insert\s+into)",
        r"(?i)(update\s+set)",
        r"(?i)(delete\s+from)",
        r"(?i)(drop\s+table)",
        r"(?i)(--\s*$)",
        r"(?i)(/\*.*\*/)",
        r"(?i)(;\s*--)",
        r"(?i)(or\s+1\s*=\s*1)",
        r"(?i)(and\s+1\s*=\s*1)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"data:",
        r"vbscript:",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"(?i)(\|\s*[;&])",
        r"(?i)(;\s*[;&])",
        r"(?i)(`.*`)",
        r"(?i)(\$\{.*\})",
        r"(?i)(\$\(",
        r"(?i)(\|\s*cat)",
        r"(?i)(\|\s*ls)",
        r"(?i)(\|\s*rm)",
    ]

    @staticmethod
    def sanitize_input(input_str: str, allowed_tags: Optional[List[str]] = None) -> str:
        """
        Sanitize input string to prevent XSS and injection attacks

        Args:
            input_str: Input string to sanitize
            allowed_tags: List of allowed HTML tags (default: no tags allowed)

        Returns:
            Sanitized string
        """
        if not input_str:
            return ""

        # Decode HTML entities
        sanitized = html.unescape(input_str)

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Strip whitespace
        sanitized = sanitized.strip()

        # Use bleach for HTML sanitization
        if allowed_tags:
            sanitized = bleach.clean(
                sanitized,
                tags=allowed_tags,
                attributes=bleach.sanitizer.ALLOWED_ATTRIBUTES,
                strip=True,
            )
        else:
            # Escape all HTML
            sanitized = html.escape(sanitized)

        return sanitized

    @staticmethod
    def validate_input(input_str: str, validation_type: str = "general") -> bool:
        """
        Validate input against common attack patterns

        Args:
            input_str: Input string to validate
            validation_type: Type of validation to perform
                - "general": General input validation
                - "sql": SQL injection prevention
                - "xss": XSS prevention
                - "command": Command injection prevention
                - "url": URL validation
                - "email": Email validation

        Returns:
            True if input is valid, False otherwise
        """
        if not input_str:
            return True

        validation_rules = {
            "sql": SecurityValidator.SQL_INJECTION_PATTERNS,
            "xss": SecurityValidator.XSS_PATTERNS,
            "command": SecurityValidator.COMMAND_INJECTION_PATTERNS,
        }

        if validation_type in validation_rules:
            patterns = validation_rules[validation_type]
            for pattern in patterns:
                if re.search(pattern, input_str, re.IGNORECASE | re.DOTALL):
                    return False

        elif validation_type == "url":
            try:
                result = urlparse(input_str)
                return all([result.scheme, result.netloc])
            except:
                return False

        elif validation_type == "email":
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            return bool(re.match(email_pattern, input_str))

        elif validation_type == "general":
            # General validation: check for suspicious patterns
            all_patterns = (
                SecurityValidator.SQL_INJECTION_PATTERNS
                + SecurityValidator.XSS_PATTERNS
                + SecurityValidator.COMMAND_INJECTION_PATTERNS
            )
            for pattern in all_patterns:
                if re.search(pattern, input_str, re.IGNORECASE | re.DOTALL):
                    return False

        return True

    @staticmethod
    def validate_json(
        input_str: str, max_depth: int = 10, max_size: int = 1000000
    ) -> bool:
        """
        Validate JSON input with size and depth limits

        Args:
            input_str: JSON string to validate
            max_depth: Maximum nesting depth
            max_size: Maximum size in bytes

        Returns:
            True if JSON is valid and within limits
        """
        if len(input_str) > max_size:
            return False

        try:
            data = json.loads(input_str)

            # Check nesting depth
            def check_depth(obj, current_depth=0):
                if current_depth > max_depth:
                    return False
                if isinstance(obj, dict):
                    for value in obj.values():
                        if not check_depth(value, current_depth + 1):
                            return False
                elif isinstance(obj, list):
                    for item in obj:
                        if not check_depth(item, current_depth + 1):
                            return False
                return True

            return check_depth(data)
        except (json.JSONDecodeError, RecursionError):
            return False

    @staticmethod
    def sanitize_dict(
        input_dict: Dict[str, Any], allowed_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sanitize dictionary values

        Args:
            input_dict: Dictionary to sanitize
            allowed_keys: List of allowed keys (if None, all keys allowed)

        Returns:
            Sanitized dictionary
        """
        if not input_dict:
            return {}

        sanitized = {}
        for key, value in input_dict.items():
            if allowed_keys and key not in allowed_keys:
                continue

            if isinstance(value, str):
                sanitized[key] = SecurityValidator.sanitize_input(value)
            elif isinstance(value, dict):
                sanitized[key] = SecurityValidator.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    SecurityValidator.sanitize_input(item)
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized


class InputValidator(BaseModel):
    """Pydantic model for input validation with security checks"""

    query: str = Field(..., min_length=1, max_length=10000)
    conversation_context: Optional[List[Dict[str, str]]] = None
    user_id: Optional[str] = None
    api_key: Optional[str] = None

    @validator("query")
    def validate_query_security(cls, v):
        """Validate query for security issues"""
        if not SecurityValidator.validate_input(v, "general"):
            raise ValueError("Query contains potentially malicious content")

        # Sanitize the query
        sanitized = SecurityValidator.sanitize_input(v)
        return sanitized

    @validator("conversation_context")
    def validate_context_security(cls, v):
        """Validate conversation context"""
        if v is None:
            return v

        sanitized_context = []
        for item in v:
            if not isinstance(item, dict):
                raise ValueError("Context items must be dictionaries")

            sanitized_item = {}
            for key, value in item.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError("Context keys and values must be strings")

                # Sanitize both key and value
                sanitized_key = SecurityValidator.sanitize_input(key)
                sanitized_value = SecurityValidator.sanitize_input(value)
                sanitized_item[sanitized_key] = sanitized_value

            sanitized_context.append(sanitized_item)

        return sanitized_context

    @validator("api_key")
    def validate_api_key_format(cls, v):
        """Validate API key format"""
        if v is None:
            return v

        # API key should be alphanumeric with underscores
        if not re.match(r"^[a-zA-Z0-9_\-]{20,100}$", v):
            raise ValueError("Invalid API key format")

        return v


def sanitize_input(input_str: str, **kwargs) -> str:
    """Convenience function for input sanitization"""
    return SecurityValidator.sanitize_input(input_str, **kwargs)


def validate_input(input_str: str, validation_type: str = "general") -> bool:
    """Convenience function for input validation"""
    return SecurityValidator.validate_input(input_str, validation_type)


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting"""

    requests_per_minute: int = Field(default=60, ge=1, le=1000)
    requests_per_hour: int = Field(default=1000, ge=10, le=10000)
    requests_per_day: int = Field(default=10000, ge=100, le=100000)
    burst_limit: int = Field(default=10, ge=1, le=100)


class SecurityConfig(BaseModel):
    """Security configuration"""

    enable_authentication: bool = True
    enable_rate_limiting: bool = True
    enable_input_validation: bool = True
    enable_audit_logging: bool = True
    secret_key: str = Field(default="change-me-in-production")
    rate_limit_config: RateLimitConfig = Field(default_factory=RateLimitConfig)
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )
    cors_enabled: bool = True

    class Config:
        env_file = ".env"
        env_prefix = "SECURITY_"
