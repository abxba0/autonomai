# SECURITY: Fix hardcoded JWT secret key in auth.py

**Labels:** `security`, `critical`, `priority-1`

## Summary

`src/security/auth.py:16` hardcodes the JWT secret key as a string literal:

```python
SECRET_KEY = "your-secret-key-change-in-production"
```

Every default installation shares the same signing key. Anyone who reads the source code (it's on GitHub) can forge valid JWT tokens for any user/role, bypassing all authentication and RBAC.

Additionally, `src/security/auth.py:128-131` contains demo credentials in production code:

```python
_demo_passwords: Dict[str, str] = {
    "admin": "password123",
    "api_client": "api_password123",
}
```

These are used in the actual `authenticate_user()` function (line 242), not just as test fixtures.

## Impact

- **Complete auth bypass** for any deployment using defaults
- Violates OWASP A07:2021 (Identification and Authentication Failures)
- Demo passwords in production code train users to accept insecure defaults

## Proposed Fix

1. **Remove the hardcoded default.** Require `SECRET_KEY` via environment variable and **fail loudly** at startup if it's missing:
   ```python
   SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
   if not SECRET_KEY:
       raise RuntimeError("JWT_SECRET_KEY environment variable is required")
   ```

2. **Remove `_demo_passwords` entirely** from `auth.py`. Move to `tests/conftest.py` as fixtures.

3. **Replace the mock user database** (lines 107-131) with an abstract interface that must be implemented by the deployment.

4. **Add a startup validation check** in `SelfOptimizingSystem.__init__` that warns if security defaults are detected.

## Files

- `src/security/auth.py` (lines 16, 107-131, 242-245)
- `web/api_secure.py` (uses auth module)
