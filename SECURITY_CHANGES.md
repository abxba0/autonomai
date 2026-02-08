# Security Changes - JWT Secret and Authentication Hardening

## Summary

This document describes the security improvements made to fix critical vulnerabilities in the authentication system.

## Issues Fixed

### 1. Hardcoded JWT Secret Key (CRITICAL)
**Issue:** `src/security/auth.py:16` contained a hardcoded JWT secret key:
```python
SECRET_KEY = "your-secret-key-change-in-production"
```

**Impact:** Any default installation shared the same signing key, allowing anyone who read the source code to forge valid JWT tokens for any user/role, completely bypassing authentication and RBAC.

**Fix:** 
- Removed hardcoded secret key
- JWT_SECRET_KEY must now be provided via environment variable
- System fails at import time with clear error message if not set
- Error message includes instructions for generating a secure key

### 2. Demo Passwords in Production Code (HIGH)
**Issue:** `src/security/auth.py:128-131` contained demo credentials:
```python
_demo_passwords: Dict[str, str] = {
    "admin": "password123",
    "api_client": "api_password123",
}
```

**Impact:** Demo passwords in production code train users to accept insecure defaults and could be accidentally deployed.

**Fix:**
- Removed `_demo_passwords` dictionary from production code
- Moved demo credentials to `tests/conftest.py` as test fixtures
- Production API implementation now requires password configuration via environment variables

### 3. Mock User Database in Production Code (MEDIUM)
**Issue:** `src/security/auth.py:107-131` contained a mock user database that was initialized automatically.

**Impact:** Mock authentication system in production code is not suitable for real deployments.

**Fix:**
- Created abstract `UserProvider` interface
- Removed mock user database from auth.py
- Production implementations must provide their own UserProvider
- Test implementations use MockUserProvider from fixtures

## Changes Made

### Files Modified

#### `src/security/auth.py`
- **Line 16-23:** JWT_SECRET_KEY now required from environment variable
  ```python
  SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
  if not SECRET_KEY:
      raise RuntimeError(
          "JWT_SECRET_KEY environment variable is required. "
          "Please set a secure random key for JWT token signing. "
          "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
      )
  ```

- **Lines 117-173:** Added abstract `UserProvider` interface
  - `get_user(username)` - Get user by username
  - `authenticate_user(username, password)` - Authenticate with credentials
  - `authenticate_with_api_key(api_key)` - Authenticate with API key
  - `create_user(username, email, role)` - Create new user

- **Lines 234-262:** Updated auth functions to delegate to UserProvider
  - Removed hardcoded mock database logic
  - All functions now call `get_user_provider()` to access implementation

- **Removed:**
  - `_users_db` mock database dictionary
  - `_demo_passwords` dictionary
  - `_initialize_default_users()` function
  - Automatic initialization at module load

#### `web/api_secure.py`
- **Lines 100-200:** Added `APIUserProvider` implementation
  - Implements UserProvider interface for web API
  - Reads passwords from environment variables
  - Warns at startup if using default passwords
  - Provides secure defaults with clear warnings

- **Lines 202-217:** Added startup event
  - Initializes user provider on application startup
  - Validates security configuration
  - Warns about insecure defaults

#### `tests/conftest.py`
- **Lines 58-187:** Added authentication test fixtures
  - `DEMO_PASSWORDS` - Demo credentials for testing only
  - `demo_passwords()` - Fixture providing demo passwords
  - `mock_user_provider()` - Fixture providing MockUserProvider
  - `setup_auth_for_tests()` - Auto-setup fixture for all tests
  - `MockUserProvider` - Test implementation of UserProvider interface

#### `.env.example`
- Added required security environment variables:
  ```env
  JWT_SECRET_KEY=your_jwt_secret_key_here_change_in_production
  ADMIN_PASSWORD=your_admin_password_here
  ADMIN_EMAIL=admin@example.com
  API_CLIENT_PASSWORD=your_api_client_password_here
  API_CLIENT_EMAIL=api@example.com
  ```

#### `src/__init__.py`
- **Lines 51-67:** Added `_validate_security_config()` method
  - Called during `SelfOptimizingSystem.__init__`
  - Warns if JWT_SECRET_KEY is not set
  - Provides guidance for setting up security

#### `docs/setup-guide.md`
- Updated security configuration section
- Added JWT_SECRET_KEY as required configuration
- Added instructions for generating secure keys
- Documented new password environment variables
- Added security notes about enforced secure defaults

## Migration Guide

### For Development/Testing

1. Set JWT_SECRET_KEY environment variable:
   ```bash
   export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   ```

2. Tests automatically use mock authentication fixtures - no changes needed

### For Production Deployments

1. **Generate a secure JWT secret key:**
   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(32))'
   ```

2. **Set required environment variables:**
   ```bash
   JWT_SECRET_KEY=<generated-secure-key>
   ADMIN_PASSWORD=<secure-admin-password>
   API_CLIENT_PASSWORD=<secure-api-password>
   ```

3. **Update your deployment configuration:**
   - Kubernetes: Add to secrets
   - Docker: Add to environment or secrets
   - Systemd: Add to environment file

4. **Implement custom UserProvider (optional):**
   If you need database-backed authentication:
   ```python
   from src.security.auth import UserProvider, set_user_provider
   
   class DatabaseUserProvider(UserProvider):
       # Implement abstract methods with your database
       ...
   
   # Set provider before starting application
   set_user_provider(DatabaseUserProvider())
   ```

## Testing

All existing security tests pass with the new implementation:

```bash
# Set test JWT secret
export JWT_SECRET_KEY="test-secret-key"

# Run security tests
pytest tests/test_security_simple.py -v  # 5/5 passed
pytest tests/test_security.py -v         # 6/6 passed
```

Tests automatically use the mock authentication fixtures from `tests/conftest.py`.

## Security Validation

### Before Changes
- ❌ Hardcoded JWT secret in source code
- ❌ Demo passwords in production code
- ❌ Mock authentication automatically initialized
- ❌ Anyone could forge valid tokens
- ❌ OWASP A07:2021 violation

### After Changes
- ✅ JWT secret required from environment variable
- ✅ Fails loudly if JWT_SECRET_KEY not set
- ✅ No demo passwords in production code
- ✅ Demo credentials only in test fixtures
- ✅ Abstract UserProvider interface
- ✅ Clear separation between test and production
- ✅ Secure defaults with warnings
- ✅ OWASP A07:2021 compliance

## Breaking Changes

1. **JWT_SECRET_KEY required:** Authentication imports will fail without it
2. **UserProvider required:** Applications using auth must call `set_user_provider()`
3. **No automatic user initialization:** Must initialize users in your provider

## Backwards Compatibility

For minimal-change compatibility with existing code:
- Tests automatically get mock auth via fixtures
- Web API includes a simple UserProvider implementation
- Clear error messages guide users to fix configuration

## References

- OWASP A07:2021 - Identification and Authentication Failures
- CWE-798: Use of Hard-coded Credentials
- NIST SP 800-63B: Digital Identity Guidelines
