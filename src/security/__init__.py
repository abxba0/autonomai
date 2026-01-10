"""
Security module for authentication, authorization, and security features
"""

from .auth import (
    User,
    Role,
    Permission,
    authenticate_user,
    create_access_token,
    get_current_user,
    require_permission,
)
from .validation import (
    sanitize_input,
    validate_input,
    InputValidator,
    SecurityValidator,
)
from .rate_limit import RateLimiter, APIKeyManager, check_rate_limit, validate_api_key
from .audit import (
    AuditLogger,
    SecurityMonitor,
    log_security_event,
    monitor_suspicious_activity,
)

__all__ = [
    # Authentication
    "User",
    "Role",
    "Permission",
    "authenticate_user",
    "create_access_token",
    "get_current_user",
    "require_permission",
    # Input validation
    "sanitize_input",
    "validate_input",
    "InputValidator",
    "SecurityValidator",
    # Rate limiting
    "RateLimiter",
    "APIKeyManager",
    "check_rate_limit",
    "validate_api_key",
    # Audit logging
    "AuditLogger",
    "SecurityMonitor",
    "log_security_event",
    "monitor_suspicious_activity",
]
