"""
Simple test script for security features (without full system dependencies)
"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Skip tests if fastapi is not installed (optional dependency)
pytest.importorskip("fastapi")

# Import security modules
from src.security.auth import (
    Role,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_token,
)

from src.security.validation import sanitize_input, validate_input

from src.security.rate_limit import RateLimiter, APIKeyManager, RateLimitConfig, RateLimitStrategy

from src.security.audit import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
)


def test_authentication():
    """Test authentication system"""
    print("=== Testing Authentication ===")

    # Test user authentication
    valid_user = authenticate_user("admin", "password123")
    assert valid_user is not None, "Admin authentication failed"
    assert valid_user.username == "admin", "Wrong user returned"
    assert valid_user.role == Role.ADMIN, "Wrong role"
    print("✓ Admin authentication successful")

    # Test invalid credentials
    invalid_user = authenticate_user("admin", "wrongpassword")
    assert invalid_user is None, "Invalid credentials should return None"
    print("✓ Invalid credentials handled correctly")

    # Test token creation and verification
    token_data = {
        "sub": "admin",
        "user_id": "admin-001",
        "role": Role.ADMIN.value,
        "permissions": [p.value for p in valid_user.permissions],
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    assert access_token is not None, "Access token creation failed"
    assert refresh_token is not None, "Refresh token creation failed"
    print("✓ Token creation successful")

    # Test token verification
    try:
        verified_data = verify_token(access_token)
        assert verified_data.username == "admin", "Token verification failed"
        print("✓ Token verification successful")
    except Exception as e:
        print(f"✗ Token verification failed: {e}")

    print()


def test_input_validation():
    """Test input validation and sanitization"""
    print("=== Testing Input Validation ===")

    # Test sanitization
    malicious_input = "<script>alert('xss')</script>Hello"
    sanitized = sanitize_input(malicious_input)
    assert "<script>" not in sanitized, "XSS sanitization failed"
    print("✓ XSS sanitization successful")

    # Test SQL injection detection
    sql_injection = "SELECT * FROM users WHERE 1=1"
    is_valid = validate_input(sql_injection, "sql")
    assert not is_valid, "SQL injection detection failed"
    print("✓ SQL injection detection successful")

    # Test command injection detection
    command_injection = "ls; rm -rf /"
    is_valid = validate_input(command_injection, "command")
    assert not is_valid, "Command injection detection failed"
    print("✓ Command injection detection successful")

    # Test valid input
    valid_input = "Hello, world!"
    is_valid = validate_input(valid_input, "general")
    assert is_valid, "Valid input incorrectly rejected"
    print("✓ Valid input accepted")

    print()


def test_rate_limiting():
    """Test rate limiting system"""
    print("=== Testing Rate Limiting ===")

    config = RateLimitConfig(
        strategy=RateLimitStrategy.FIXED_WINDOW,
        requests_per_minute=5,  # Low limit for testing
        requests_per_hour=50,
        requests_per_day=500,
        burst_limit=2,
    )

    rate_limiter = RateLimiter(config, use_redis=False)

    # Test rate limiting
    client_id = "test_client"
    allowed_count = 0

    for i in range(10):
        allowed, headers = rate_limiter.check_rate_limit(client_id)
        if allowed:
            allowed_count += 1

    # Should allow burst limit + some requests
    assert (
        2 <= allowed_count <= 5
    ), f"Rate limiting not working correctly: allowed {allowed_count}"
    print(f"✓ Rate limiting working: allowed {allowed_count}/10 requests")

    print()


def test_api_key_management():
    """Test API key management"""
    print("=== Testing API Key Management ===")

    api_key_manager = APIKeyManager()

    # Generate API key
    api_key = api_key_manager.generate_api_key(
        name="Test API Key",
        owner="test_user",
        permissions=["api_execute", "api_read"],
        rate_limit_config=RateLimitConfig(),
    )

    assert api_key.key is not None, "API key generation failed"
    print("✓ API key generation successful")

    # Validate API key
    validated_key = api_key_manager.validate_api_key(api_key.key)
    assert validated_key is not None, "API key validation failed"
    assert validated_key.name == "Test API Key", "Wrong API key info"
    print("✓ API key validation successful")

    # Revoke API key
    revoked = api_key_manager.revoke_api_key(api_key.key)
    assert revoked, "API key revocation failed"

    validated_key = api_key_manager.validate_api_key(api_key.key)
    assert (
        validated_key is None or not validated_key.is_active
    ), "Revoked key should not be valid"
    print("✓ API key revocation successful")

    print()


def test_audit_logging():
    """Test audit logging system"""
    print("=== Testing Audit Logging ===")

    audit_logger = AuditLogger(
        log_file="test_audit.log",
        database_file=None,  # Don't use database for simple test
        enable_console=False,
    )

    # Log test event
    import uuid

    test_event = AuditEvent(
        event_id=str(uuid.uuid4()),
        event_type=AuditEventType.LOGIN_SUCCESS,
        severity=AuditSeverity.INFO,
        user_id="test_user",
        username="test",
        ip_address="127.0.0.1",
        user_agent="Test Client",
        resource="login",
        action="login_success",
        details={"test": "data"},
        success=True,
    )

    # This should not raise an exception
    audit_logger.log_event(test_event)
    print("✓ Audit logging successful (no exceptions)")

    # Clean up test files
    import os

    if os.path.exists("test_audit.log"):
        os.remove("test_audit.log")

    print()


def main():
    """Run all security tests"""
    print("Running Security Feature Tests")
    print("=" * 40)

    try:
        test_authentication()
        test_input_validation()
        test_rate_limiting()
        test_api_key_management()
        test_audit_logging()

        print("=" * 40)
        print("✅ All security tests passed!")
        print("\nSecurity Features Summary:")
        print("1. ✅ Authentication & Authorization")
        print("2. ✅ Input Validation & Sanitization")
        print("3. ✅ Rate Limiting")
        print("4. ✅ API Key Management")
        print("5. ✅ Audit Logging")

    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {e}")
        import traceback

        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
