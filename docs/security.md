# Security Guide

Comprehensive guide to security features in the Self-Optimizing Instruction Library.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Authorization](#authorization)
- [Rate Limiting](#rate-limiting)
- [Input Validation](#input-validation)
- [Audit Logging](#audit-logging)
- [Best Practices](#best-practices)
- [Security Configuration](#security-configuration)

## Overview

The Self-Optimizing Instruction Library includes enterprise-grade security features:

- **JWT Token-based Authentication**: Secure user authentication with refresh tokens
- **Role-Based Access Control (RBAC)**: Fine-grained permission management
- **Rate Limiting**: Protection against API abuse with multiple strategies
- **Input Validation & Sanitization**: XSS, SQL injection, and command injection prevention
- **Audit Logging**: Comprehensive tracking of all security-relevant events
- **API Key Management**: Secure key generation and revocation

## Authentication

### JWT Token Authentication

The system uses JSON Web Tokens (JWT) for stateless authentication.

#### Registering a User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "SecurePassword123!",
    "email": "alice@example.com",
    "role": "editor"
  }'
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

#### Logging In

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "SecurePassword123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Using Access Tokens

Include the access token in the Authorization header:

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -d '{"query": "What is AI?"}'
```

#### Refreshing Tokens

Access tokens expire after 1 hour. Use refresh tokens to get new access tokens:

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

### API Key Authentication

Alternative authentication method using API keys.

#### Creating API Keys

```bash
curl -X POST http://localhost:8000/auth/api-keys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "permissions": ["execute", "read"],
    "rate_limit": {
      "requests_per_minute": 100
    }
  }'
```

**Response:**
```json
{
  "api_key": "sk_live_1234567890abcdef",
  "key_id": "key_001",
  "name": "Production API Key",
  "created_at": "2025-01-10T15:00:00Z"
}
```

#### Using API Keys

```bash
curl -X POST http://localhost:8000/execute \
  -H "X-API-Key: sk_live_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AI?"}'
```

#### Revoking API Keys

```bash
curl -X DELETE http://localhost:8000/auth/api-keys/key_001 \
  -H "Authorization: Bearer <token>"
```

## Authorization

### Roles

The system supports four built-in roles:

1. **Admin**
   - Full system access
   - User management
   - Security configuration
   - Audit log access

2. **Editor**
   - Execute queries
   - Submit feedback
   - Request instruction updates
   - View version history

3. **Viewer**
   - Execute queries (read-only)
   - View status
   - View version history

4. **API_Client**
   - Programmatic access
   - Execute queries
   - Custom rate limits

### Permissions

Fine-grained permissions control access to specific operations:

- `execute`: Execute queries
- `feedback`: Submit feedback
- `optimize`: Trigger manual optimization
- `rollback`: Rollback versions
- `admin`: Administrative operations
- `audit`: View audit logs

### Checking Permissions

```python
from src.security import has_permission

if has_permission(user, "execute"):
    result = system.execute(query)
else:
    raise PermissionError("User lacks execute permission")
```

### Custom Roles

Create custom roles with specific permissions:

```python
from src.security import Role, Permission

custom_role = Role(
    name="DataScientist",
    permissions=[
        Permission.EXECUTE,
        Permission.FEEDBACK,
        Permission.VIEW_HISTORY
    ]
)
```

## Rate Limiting

### Rate Limiting Strategies

The system supports multiple rate limiting strategies:

1. **Fixed Window**
   - Simple counting in fixed time windows
   - Fast and memory efficient
   - May allow burst at window boundaries

2. **Sliding Window**
   - Smooths out burst traffic
   - More accurate than fixed window
   - Slightly more resource intensive

3. **Token Bucket**
   - Allows controlled bursts
   - Flexible and fair
   - Configurable bucket size and refill rate

### Configuration

```python
from src.security import RateLimitConfig

rate_config = RateLimitConfig(
    strategy="sliding_window",  # or "fixed_window", "token_bucket"
    requests_per_minute=60,
    requests_per_hour=1000,
    requests_per_day=10000,
    burst_size=10  # For token bucket strategy
)
```

### Response Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1704902400
```

### Handling Rate Limits

When rate limited, the API returns 429 status:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 30,
  "limit": 60,
  "window": "1 minute"
}
```

### Per-User Rate Limits

Different limits for different roles:

```python
ROLE_RATE_LIMITS = {
    "admin": RateLimitConfig(requests_per_minute=1000),
    "editor": RateLimitConfig(requests_per_minute=100),
    "viewer": RateLimitConfig(requests_per_minute=60),
    "api_client": RateLimitConfig(requests_per_minute=500)
}
```

## Input Validation

### XSS Prevention

All user inputs are sanitized to prevent cross-site scripting:

```python
from src.security import sanitize_input

safe_query = sanitize_input(user_query)
```

**Blocked Content:**
- `<script>` tags
- `javascript:` URLs
- Event handlers (onclick, onerror, etc.)
- Data URIs with executable content

### SQL Injection Detection

Inputs are checked for SQL injection patterns:

```python
from src.security import check_sql_injection

if check_sql_injection(query):
    raise SecurityError("Potential SQL injection detected")
```

**Detected Patterns:**
- UNION SELECT statements
- DROP TABLE commands
- Comment sequences (-- and /* */)
- String concatenation attacks

### Command Injection Prevention

Shell commands are validated before execution:

```python
from src.security import validate_command

if not validate_command(command):
    raise SecurityError("Invalid command detected")
```

**Blocked Characters:**
- Semicolons (;)
- Pipes (|)
- Redirects (>, <, >>)
- Command substitution ($(), ``)
- Background execution (&)

### JSON Validation

JSON inputs are validated for size and structure:

```python
from src.security import validate_json

validated_data = validate_json(
    json_string,
    max_size=1048576,  # 1MB
    max_depth=10
)
```

**Limits:**
- Maximum size: 1MB (configurable)
- Maximum nesting depth: 10 levels
- No circular references

### Pydantic Models

All API inputs use Pydantic for type-safe validation:

```python
from pydantic import BaseModel, validator

class ExecuteRequest(BaseModel):
    query: str
    include_metadata: bool = False
    
    @validator('query')
    def validate_query(cls, v):
        if len(v) < 1:
            raise ValueError("Query cannot be empty")
        if len(v) > 10000:
            raise ValueError("Query too long")
        return v
```

## Audit Logging

### Event Types

The system logs 20+ security-relevant events:

**Authentication Events:**
- `user_login`
- `user_logout`
- `login_failed`
- `token_refresh`
- `api_key_created`
- `api_key_revoked`

**Authorization Events:**
- `permission_denied`
- `role_changed`

**System Events:**
- `query_executed`
- `feedback_submitted`
- `instruction_updated`
- `version_rollback`
- `rate_limit_exceeded`

**Security Events:**
- `suspicious_activity`
- `xss_attempt`
- `sql_injection_attempt`
- `command_injection_attempt`

### Viewing Audit Logs

```bash
# Get recent logs
curl http://localhost:8000/admin/audit-logs \
  -H "Authorization: Bearer <admin_token>"

# Filter by event type
curl "http://localhost:8000/admin/audit-logs?event_type=user_login" \
  -H "Authorization: Bearer <admin_token>"

# Filter by time range
curl "http://localhost:8000/admin/audit-logs?since=2025-01-10T00:00:00Z" \
  -H "Authorization: Bearer <admin_token>"
```

### Log Format

```json
{
  "id": "log_12345",
  "timestamp": "2025-01-10T15:00:00Z",
  "event_type": "user_login",
  "user_id": "user_001",
  "username": "alice",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "details": {
    "success": true,
    "method": "password"
  }
}
```

### Monitoring and Alerts

#### Real-time Security Monitoring

```python
from src.security import SecurityMonitor

monitor = SecurityMonitor()

# Get security events in real-time
for event in monitor.stream_events():
    if event.severity == "critical":
        send_alert(event)
```

#### Security Reports

```bash
# Generate security report
curl http://localhost:8000/admin/security-report \
  -H "Authorization: Bearer <admin_token>"
```

**Report Includes:**
- Failed login attempts
- Rate limit violations
- Permission denials
- Suspicious activity patterns
- Recommendations

## Best Practices

### 1. Strong Secret Keys

Generate secure random keys:

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

Store in environment variables, never in code:

```bash
# .env
SECRET_KEY=your_generated_key_here
```

### 2. HTTPS in Production

Always use HTTPS in production:

```python
# Use reverse proxy (nginx, Apache)
# Or configure uvicorn with SSL
uvicorn.run(
    app,
    host="0.0.0.0",
    port=443,
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem"
)
```

### 3. CORS Configuration

Restrict CORS to specific origins:

```python
ALLOWED_ORIGINS = [
    "https://app.example.com",
    "https://admin.example.com"
]
```

Never use `*` in production:

```python
# DON'T DO THIS IN PRODUCTION
ALLOWED_ORIGINS = ["*"]
```

### 4. Token Expiration

Use short-lived access tokens:

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 7    # 1 week
```

### 5. Password Policies

Enforce strong password requirements:

```python
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL = True
```

### 6. Regular Security Audits

Schedule regular security reviews:

- Review audit logs weekly
- Check for failed login attempts
- Monitor rate limit violations
- Update dependencies regularly
- Rotate API keys periodically

### 7. Input Sanitization

Always sanitize user inputs:

```python
from src.security import sanitize_input

# Sanitize all user inputs
safe_query = sanitize_input(request.query)
safe_feedback = sanitize_input(request.feedback)
```

### 8. Least Privilege

Grant minimum necessary permissions:

```python
# Grant only required permissions
user = create_user(
    username="analyst",
    role="viewer"  # Read-only access
)
```

### 9. Monitoring and Alerting

Set up real-time alerts for security events:

```python
from src.security import setup_alerts

setup_alerts(
    events=["login_failed", "permission_denied", "rate_limit_exceeded"],
    threshold=5,  # Alert after 5 events
    window_minutes=10
)
```

### 10. Defense in Depth

Use multiple security layers:

- Authentication (JWT + API keys)
- Authorization (RBAC)
- Rate limiting
- Input validation
- Audit logging
- Network security (firewall, HTTPS)

## Security Configuration

### Complete Security Setup

```python
from src.security import SecurityConfig, RateLimitConfig

SECURITY_CONFIG = SecurityConfig(
    # Authentication
    enable_authentication=True,
    secret_key=os.getenv("SECRET_KEY"),
    access_token_expire_minutes=60,
    refresh_token_expire_days=7,
    
    # Authorization
    enable_authorization=True,
    default_role="viewer",
    
    # Rate Limiting
    enable_rate_limiting=True,
    rate_limit_config=RateLimitConfig(
        strategy="sliding_window",
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000
    ),
    
    # Input Validation
    enable_input_validation=True,
    max_query_length=10000,
    max_json_size=1048576,  # 1MB
    
    # Audit Logging
    enable_audit_logging=True,
    audit_log_retention_days=90,
    
    # CORS
    allowed_origins=[
        "https://app.example.com",
        "https://admin.example.com"
    ],
    
    # Security Headers
    enable_security_headers=True
)
```

### Environment Variables

```env
# Security
SECRET_KEY=your_secret_key_here
ENABLE_AUTHENTICATION=true
ENABLE_RATE_LIMITING=true
ENABLE_AUDIT_LOGGING=true

# Token Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
RATE_LIMIT_STRATEGY=sliding_window
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# CORS
ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com

# Redis (for distributed rate limiting)
REDIS_URL=redis://localhost:6379/0
```

## Compliance

### GDPR Considerations

For GDPR compliance:

1. **Data Minimization**: Only collect necessary user data
2. **Right to Access**: Provide user data upon request
3. **Right to Erasure**: Implement user data deletion
4. **Data Portability**: Export user data in standard format
5. **Audit Logs**: Maintain records of data processing

### SOC 2 Considerations

For SOC 2 compliance:

1. **Access Controls**: Implement RBAC
2. **Audit Logging**: Comprehensive event logging
3. **Encryption**: Use HTTPS and encrypt sensitive data
4. **Incident Response**: Monitor and respond to security events
5. **Change Management**: Track all system changes

## Security Checklist

Before deploying to production:

- [ ] Generate strong SECRET_KEY
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS with specific origins
- [ ] Enable authentication and authorization
- [ ] Set up rate limiting
- [ ] Enable audit logging
- [ ] Configure input validation
- [ ] Set up monitoring and alerts
- [ ] Review and test security controls
- [ ] Document security procedures
- [ ] Plan incident response
- [ ] Regular security audits

## Next Steps

- Review [Setup Guide](setup-guide.md) for configuration
- Check [API Reference](api-reference.md) for authentication endpoints
- See [Troubleshooting](troubleshooting.md) for security issues
