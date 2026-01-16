"""
Security module for authentication, authorization, and security features
"""

from .auth import (
    User,
    Role,
    Permission,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_user,
    get_current_user,
    require_permission,
)
from .validation import (
    sanitize_input,
    validate_input,
    InputValidator,
    SecurityValidator,
    SecurityConfig,
)
from .rate_limit import (
    RateLimiter,
    APIKeyManager,
    RateLimitConfig,
    RateLimitStrategy,
    check_rate_limit,
    validate_api_key,
)
from .audit import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    SecurityMonitor,
    log_security_event,
    monitor_suspicious_activity,
)
from .gdpr import (
    GDPRCompliance,
    ConsentPurpose,
    ConsentRecord,
    DataAccessRequest,
    DataDeletionRequest,
    DataExportFormat,
)

__all__ = [
    # Authentication
    "User",
    "Role",
    "Permission",
    "authenticate_user",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_user",
    "get_current_user",
    "require_permission",
    # Input validation
    "sanitize_input",
    "validate_input",
    "InputValidator",
    "SecurityValidator",
    "SecurityConfig",
    # Rate limiting
    "RateLimiter",
    "APIKeyManager",
    "RateLimitConfig",
    "RateLimitStrategy",
    "check_rate_limit",
    "validate_api_key",
    # Audit logging
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity",
    "SecurityMonitor",
    "log_security_event",
    "monitor_suspicious_activity",
    # GDPR Compliance
    "GDPRCompliance",
    "ConsentPurpose",
    "ConsentRecord",
    "DataAccessRequest",
    "DataDeletionRequest",
    "DataExportFormat",
]
