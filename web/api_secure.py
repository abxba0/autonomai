"""
Secure FastAPI web interface for the Self-Optimizing Instruction Library
with authentication, authorization, rate limiting, and input validation
"""

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import uvicorn
import os
import secrets
import time
from dotenv import load_dotenv
from datetime import datetime

# Add parent directory to path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem, SystemConfig
from src.security import (
    # Authentication
    User,
    Role,
    Permission,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_user,
    SecurityValidator,
    SecurityConfig,
    # Rate limiting
    RateLimiter,
    APIKeyManager,
    RateLimitConfig,
    AuditLogger,
    SecurityMonitor,
    log_security_event,
    AuditEventType,
    AuditSeverity,
)

# Load environment variables
load_dotenv()

# Security configuration
SECURITY_CONFIG = SecurityConfig(
    enable_authentication=True,
    enable_rate_limiting=True,
    enable_input_validation=True,
    enable_audit_logging=True,
    secret_key=os.getenv("SECRET_KEY", "change-me-in-production"),
    rate_limit_config=RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000,
        burst_limit=10,
    ),
    allowed_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    cors_enabled=True,
)

# Create FastAPI app
app = FastAPI(
    title="Self-Optimizing Instruction Library API (Secure)",
    description="Secure API for the self-optimizing AI instruction system",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
)

# Add CORS middleware
if SECURITY_CONFIG.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=SECURITY_CONFIG.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

# Security instances
security = HTTPBearer()
rate_limiter = RateLimiter(SECURITY_CONFIG.rate_limit_config)
api_key_manager = APIKeyManager()
audit_logger = AuditLogger(
    log_file="audit.log", database_file="audit.db", enable_console=True
)
security_monitor = SecurityMonitor(audit_logger)


# User Provider Implementation for API
from src.security.auth import (
    UserProvider,
    set_user_provider,
    ROLE_PERMISSIONS,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)


class APIUserProvider(UserProvider):
    """
    In-memory user provider for API authentication.
    
    WARNING: This is a simple implementation for demonstration.
    For production, implement a proper database-backed user provider
    with secure password hashing (e.g., bcrypt, argon2).
    """
    
    def __init__(self):
        self.users_db = {}
        # In production, passwords should be loaded from environment or secure storage
        # and hashed with bcrypt/argon2
        admin_password = os.getenv("ADMIN_PASSWORD")
        api_client_password = os.getenv("API_CLIENT_PASSWORD")
        
        # Fail if passwords not set (instead of using insecure defaults)
        if not admin_password:
            raise RuntimeError(
                "ADMIN_PASSWORD environment variable is required. "
                "Please set a secure password for the admin user."
            )
        if not api_client_password:
            raise RuntimeError(
                "API_CLIENT_PASSWORD environment variable is required. "
                "Please set a secure password for the API client user."
            )
        
        self.passwords = {
            "admin": admin_password,
            "api_client": api_client_password,
        }
        self._initialize_users()
    
    def _initialize_users(self):
        """Initialize default users"""
        # Create admin user
        admin_user = User(
            id="admin-001",
            username="admin",
            email=os.getenv("ADMIN_EMAIL", "admin@example.com"),
            role=Role.ADMIN,
            permissions=ROLE_PERMISSIONS[Role.ADMIN],
            is_active=True,
        )
        self.users_db[admin_user.username] = admin_user
        
        # Create API client user with generated key
        # Note: API key should be retrieved via secure administrative endpoint
        # or key management system in production
        api_key = generate_api_key()
        api_client = User(
            id="api-001",
            username="api_client",
            email=os.getenv("API_CLIENT_EMAIL", "api@example.com"),
            role=Role.API_CLIENT,
            permissions=ROLE_PERMISSIONS[Role.API_CLIENT],
            api_key=api_key,
            api_key_hash=hash_api_key(api_key),
            is_active=True,
        )
        self.users_db[api_client.username] = api_client
    
    def get_user(self, username: str):
        return self.users_db.get(username)
    
    def authenticate_user(self, username: str, password: str):
        user = self.users_db.get(username)
        if not user or not user.is_active:
            return None
        
        # In production, use proper password hashing (bcrypt.checkpw)
        expected_password = self.passwords.get(username)
        # Use constant-time comparison to prevent timing attacks
        if expected_password and secrets.compare_digest(password, expected_password):
            return user
        return None
    
    def authenticate_with_api_key(self, api_key: str):
        for user in self.users_db.values():
            if user.api_key_hash and verify_api_key(api_key, user.api_key_hash):
                return user
        return None
    
    def create_user(self, username: str, email: str, role: Role):
        if username in self.users_db:
            raise ValueError(f"User {username} already exists")
        
        user = User(
            id=f"user-{len(self.users_db) + 1:03d}",
            username=username,
            email=email,
            role=role,
            permissions=ROLE_PERMISSIONS[role],
            is_active=True,
        )
        self.users_db[username] = user
        return user


# Initialize user provider on startup
@app.on_event("startup")
async def startup_event():
    """Initialize authentication system on startup"""
    user_provider = APIUserProvider()
    set_user_provider(user_provider)
    
    print("✓ Authentication system initialized")
    
    # Note: API key for api_client user is stored securely
    # For initial setup, retrieve via secure administrative endpoint or key management system


# Pydantic models for API requests/responses
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes


class ExecuteRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    conversation_context: Optional[List[Dict[str, str]]] = None

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


class ExecuteResponse(BaseModel):
    output: str
    validation_passed: bool
    validation_results: List[Dict[str, Any]]
    optimization_attempted: bool
    optimization_result: Optional[Dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    feedback: str = Field(..., min_length=1, max_length=5000)
    severity: str = Field(default="moderate", regex="^(low|moderate|high|critical)$")
    attach_last_output: bool = True

    @validator("feedback")
    def validate_feedback_security(cls, v):
        """Validate feedback for security issues"""
        if not SecurityValidator.validate_input(v, "general"):
            raise ValueError("Feedback contains potentially malicious content")

        # Sanitize the feedback
        sanitized = SecurityValidator.sanitize_input(v)
        return sanitized


class VersionInfo(BaseModel):
    version_id: str
    timestamp: str
    trigger_type: str
    diff_summary: str
    rules_added: int
    rules_modified: int
    rules_deprecated: int


class SystemStatus(BaseModel):
    total_failures: int
    total_optimizations: int
    current_version: Optional[str]
    last_optimization: Optional[str]
    system_health: str


class UserInfo(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str]


class APIKeyInfo(BaseModel):
    name: str
    owner: str
    permissions: List[str]
    created_at: str
    last_used: Optional[str]
    is_active: bool
    expires_at: Optional[str]


# Global system instance
_system_instance = None


def get_system():
    """Get or create system instance"""
    global _system_instance
    if _system_instance is None:
        # Configure system
        config = SystemConfig(
            main_model=os.getenv("MAIN_MODEL", "claude-3-5-sonnet-20241022"),
            critic_model=os.getenv("CRITIC_MODEL", "claude-3-haiku-20240307"),
            enable_auto_optimization=True,
        )
        _system_instance = SelfOptimizingSystem(config)
    return _system_instance


# Dependency functions
async def get_client_id(request: Request) -> str:
    """Get client ID for rate limiting"""
    # Use IP address as client ID
    client_ip = request.client.host if request.client else "unknown"

    # If authenticated, use user ID
    user = await get_current_user_or_api_key(request)
    if user:
        return f"user:{user.id}"

    return f"ip:{client_ip}"


async def get_current_user_or_api_key(request: Request) -> Optional[User]:
    """Get current user or authenticate with API key"""
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    # Check for Bearer token
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

        # Check if it's an API key (starts with sk_)
        if token.startswith("sk_"):
            api_key_info = api_key_manager.validate_api_key(token)
            if api_key_info:
                # Create a user object from API key info
                user = User(
                    id=f"api:{api_key_info.key_hash[:8]}",
                    username=f"api_{api_key_info.owner}",
                    email=f"{api_key_info.owner}@api.example.com",
                    role=Role.API_CLIENT,
                    permissions=api_key_info.permissions,
                    is_active=api_key_info.is_active,
                )

                # Log API key usage
                log_security_event(
                    event_type=AuditEventType.API_KEY_USED,
                    severity=AuditSeverity.INFO,
                    user_id=user.id,
                    username=user.username,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent"),
                    resource="api",
                    action="api_key_used",
                    details={"api_key_name": api_key_info.name},
                    success=True,
                )

                return user

        # Otherwise, treat as JWT token
        try:
            token_data = verify_token(token)
            user = get_user(token_data.username)
            return user
        except HTTPException:
            return None

    return None


async def require_auth(user: Optional[User] = Depends(get_current_user_or_api_key)):
    """Require authentication"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def apply_rate_limit(request: Request, client_id: str = Depends(get_client_id)):
    """Apply rate limiting"""
    if SECURITY_CONFIG.enable_rate_limiting:
        allowed, headers = rate_limiter.check_rate_limit(client_id, request.url.path)

        if not allowed:
            # Log rate limit violation
            log_security_event(
                event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                severity=AuditSeverity.WARNING,
                user_id=client_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
                resource=request.url.path,
                action="rate_limit_exceeded",
                details={
                    "client_id": client_id,
                    "endpoint": request.url.path,
                    "method": request.method,
                },
                success=False,
                error_message="Rate limit exceeded",
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers=headers,
            )

        return headers

    return {}


# Middleware for security monitoring
@app.middleware("http")
async def security_monitoring_middleware(request: Request, call_next):
    """Middleware for security monitoring and audit logging"""
    start_time = time.time()

    # Get client info
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "")

    try:
        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log successful request
        if SECURITY_CONFIG.enable_audit_logging:
            # Get user info if available
            user = await get_current_user_or_api_key(request)
            user_id = user.id if user else None
            username = user.username if user else None

            # Log the request
            log_security_event(
                event_type=(
                    AuditEventType.QUERY_EXECUTED
                    if request.url.path == "/execute"
                    else AuditEventType.SECURITY_ALERT
                ),
                severity=AuditSeverity.INFO,
                user_id=user_id,
                username=username,
                ip_address=client_ip,
                user_agent=user_agent,
                resource=request.url.path,
                action=request.method.lower(),
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "query_params": dict(request.query_params),
                },
                success=response.status_code < 400,
            )

        return response

    except Exception as e:
        # Log error
        if SECURITY_CONFIG.enable_audit_logging:
            log_security_event(
                event_type=AuditEventType.SECURITY_ALERT,
                severity=AuditSeverity.ERROR,
                ip_address=client_ip,
                user_agent=user_agent,
                resource=request.url.path,
                action=request.method.lower(),
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
                success=False,
                error_message=str(e),
            )

        raise


# Public endpoints (no authentication required)
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Self-Optimizing Instruction Library API (Secure)",
        "version": "2.0.0",
        "security": {
            "authentication": SECURITY_CONFIG.enable_authentication,
            "rate_limiting": SECURITY_CONFIG.enable_rate_limiting,
            "input_validation": SECURITY_CONFIG.enable_input_validation,
            "audit_logging": SECURITY_CONFIG.enable_audit_logging,
        },
        "endpoints": [
            "/login - Authenticate and get tokens",
            "/refresh - Refresh access token",
            "/execute - Execute query (requires auth)",
            "/feedback - Provide feedback (requires auth)",
            "/status - System status (requires auth)",
            "/versions - Version history (requires auth)",
            "/instructions - Current instructions (requires auth)",
            "/health - Health check",
            "/security/report - Security report (admin only)",
        ],
    }


@app.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest, rate_limit_headers: dict = Depends(apply_rate_limit)
):
    """Authenticate user and get tokens"""
    # Validate input
    if not SecurityValidator.validate_input(request.username, "general"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username format",
        )

    if not SecurityValidator.validate_input(request.password, "general"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password format",
        )

    # Authenticate user
    user = authenticate_user(request.username, request.password)

    if not user:
        # Log failed login attempt
        log_security_event(
            event_type=AuditEventType.LOGIN_FAILURE,
            severity=AuditSeverity.WARNING,
            username=request.username,
            ip_address=(
                request.client.host
                if hasattr(request, "client") and request.client
                else None
            ),
            resource="login",
            action="login_attempt",
            details={"username": request.username},
            success=False,
            error_message="Invalid credentials",
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "role": user.role.value,
        "permissions": [p.value for p in user.permissions],
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Log successful login
    log_security_event(
        event_type=AuditEventType.LOGIN_SUCCESS,
        severity=AuditSeverity.INFO,
        user_id=user.id,
        username=user.username,
        ip_address=(
            request.client.host
            if hasattr(request, "client") and request.client
            else None
        ),
        resource="login",
        action="login_success",
        details={"role": user.role.value},
        success=True,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800,
    )


@app.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str, rate_limit_headers: dict = Depends(apply_rate_limit)
):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        token_data = verify_token(refresh_token)

        # Get user
        user = get_user(token_data.username)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Create new tokens
        new_token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
        }

        new_access_token = create_access_token(new_token_data)
        new_refresh_token = create_refresh_token(new_token_data)

        # Log token refresh
        log_security_event(
            event_type=AuditEventType.TOKEN_REFRESH,
            severity=AuditSeverity.INFO,
            user_id=user.id,
            username=user.username,
            resource="auth",
            action="token_refresh",
            success=True,
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=1800,
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "self-optimizing-system",
        "timestamp": datetime.utcnow().isoformat(),
        "security_enabled": SECURITY_CONFIG.enable_authentication,
    }


# Protected endpoints (require authentication)
@app.post("/execute", response_model=ExecuteResponse)
async def execute_query(
    request: ExecuteRequest,
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
    system: SelfOptimizingSystem = Depends(get_system),
):
    """Execute a query with the system (requires authentication)"""
    # Check permission
    if not user.has_permission(Permission.EXECUTE_QUERY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: execute_query required",
        )

    try:
        result = system.execute(
            user_query=request.query, conversation_context=request.conversation_context
        )

        return ExecuteResponse(
            output=result["output"],
            validation_passed=result["validation_passed"],
            validation_results=[
                {
                    "validator_name": r.validator_name,
                    "passed": r.passed,
                    "error_message": r.error_message,
                }
                for r in result["validation_results"]
            ],
            optimization_attempted=result.get("optimization_attempted", False),
            optimization_result=result.get("optimization_result"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


@app.post("/feedback")
async def provide_feedback(
    request: FeedbackRequest,
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
    system: SelfOptimizingSystem = Depends(get_system),
):
    """Provide manual feedback for system improvement (requires authentication)"""
    # Check permission
    if not user.has_permission(Permission.EDIT_INSTRUCTIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: edit_instructions required",
        )

    try:
        result = system.request_instruction_update(
            user_feedback=request.feedback,
            severity=request.severity,
            attach_last_output=request.attach_last_output,
        )

        return {
            "success": result.get("success", False),
            "message": result.get("message", "Feedback processed"),
            "optimization_result": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback error: {str(e)}")


@app.get("/status", response_model=SystemStatus)
async def get_status(
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
    system: SelfOptimizingSystem = Depends(get_system),
):
    """Get system status (requires authentication)"""
    # Check permission
    if not user.has_permission(Permission.VIEW_METRICS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: view_metrics required",
        )

    try:
        # Get version history
        history = system.get_version_history()

        # Calculate metrics
        total_optimizations = len(
            [v for v in history if v["trigger_type"] != "initial"]
        )
        last_optimization = history[-1]["timestamp"] if history else None

        return SystemStatus(
            total_failures=len(system.instruction_manager.failure_log.entries),
            total_optimizations=total_optimizations,
            current_version=system.instruction_manager.current_version,
            last_optimization=last_optimization,
            system_health="healthy" if total_optimizations > 0 else "initializing",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")


@app.get("/versions", response_model=List[VersionInfo])
async def get_versions(
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
    system: SelfOptimizingSystem = Depends(get_system),
):
    """Get version history (requires authentication)"""
    # Check permission
    if not user.has_permission(Permission.VIEW_INSTRUCTIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: view_instructions required",
        )

    try:
        history = system.get_version_history()
        return [
            VersionInfo(
                version_id=v["version_id"],
                timestamp=v["timestamp"],
                trigger_type=v["trigger_type"],
                diff_summary=v["diff_summary"],
                rules_added=v["rules_added"],
                rules_modified=v["rules_modified"],
                rules_deprecated=v["rules_deprecated"],
            )
            for v in history
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Versions error: {str(e)}")


@app.get("/instructions")
async def get_instructions(
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
    system: SelfOptimizingSystem = Depends(get_system),
):
    """Get current instructions (requires authentication)"""
    # Check permission
    if not user.has_permission(Permission.VIEW_INSTRUCTIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: view_instructions required",
        )

    try:
        instructions = system.get_current_instructions()
        return {
            "instructions": instructions,
            "length": len(instructions),
            "current_version": system.instruction_manager.current_version,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Instructions error: {str(e)}")


@app.post("/rollback/{steps}")
async def rollback_version(
    steps: int,
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
    system: SelfOptimizingSystem = Depends(get_system),
):
    """Rollback to previous version (requires authentication)"""
    # Check permission
    if not user.has_permission(Permission.EDIT_INSTRUCTIONS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: edit_instructions required",
        )

    try:
        success = system.rollback(steps)
        return {
            "success": success,
            "message": (
                f"Rolled back {steps} versions" if success else "Rollback failed"
            ),
            "current_version": (
                system.instruction_manager.current_version if success else None
            ),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback error: {str(e)}")


# Admin endpoints
@app.get("/security/report")
async def get_security_report(
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
    hours: int = 24,
):
    """Get security report (admin only)"""
    # Check permission
    if not user.has_permission(Permission.MANAGE_SYSTEM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: manage_system required",
        )

    try:
        report = security_monitor.get_security_report(hours=hours)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Security report error: {str(e)}")


@app.get("/admin/users", response_model=List[UserInfo])
async def list_users(
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
):
    """List all users (admin only)"""
    # Check permission
    if not user.has_permission(Permission.MANAGE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: manage_users required",
        )

    # This would query a real user database in production
    # For now, return empty list
    return []


@app.get("/admin/api-keys", response_model=List[APIKeyInfo])
async def list_api_keys(
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
):
    """List API keys (admin only)"""
    # Check permission
    if not user.has_permission(Permission.MANAGE_SYSTEM):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: manage_system required",
        )

    try:
        api_keys = api_key_manager.list_api_keys()
        return [
            APIKeyInfo(
                name=key.name,
                owner=key.owner,
                permissions=key.permissions,
                created_at=key.created_at.isoformat(),
                last_used=key.last_used.isoformat() if key.last_used else None,
                is_active=key.is_active,
                expires_at=key.expires_at.isoformat() if key.expires_at else None,
            )
            for key in api_keys
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API keys error: {str(e)}")


# GDPR Compliance Endpoints
from src.security.gdpr import (
    GDPRCompliance,
    ConsentPurpose,
    DataExportFormat,
)


# GDPR instance (initialized lazily with database manager)
_gdpr_instance = None


def get_gdpr():
    """Get or create GDPR compliance instance"""
    global _gdpr_instance
    if _gdpr_instance is None:
        _gdpr_instance = GDPRCompliance(
            database_manager=None,
            audit_logger=audit_logger,
        )
    return _gdpr_instance


class ConsentRequest(BaseModel):
    purpose: str = Field(..., description="Consent purpose")
    version: str = Field(default="1.0", description="Privacy policy version")
    method: str = Field(default="web", description="Consent method")


class RectifyRequest(BaseModel):
    field: str = Field(..., description="Field to update (email or username)")
    new_value: str = Field(..., min_length=1, max_length=255)


class DeletionRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=1000)


@app.post("/gdpr/consent")
async def grant_consent(
    request: Request,
    consent_req: ConsentRequest,
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
):
    """Grant consent for a specific purpose"""
    try:
        purpose = ConsentPurpose(consent_req.purpose)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid purpose. Valid options: {[p.value for p in ConsentPurpose]}",
        )

    gdpr = get_gdpr()
    consent = gdpr.grant_consent(
        user_id=user.id,
        purpose=purpose,
        version=consent_req.version,
        method=consent_req.method,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return {"success": True, "consent": consent.to_dict()}


@app.delete("/gdpr/consent/{purpose}")
async def withdraw_consent(
    purpose: str,
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
):
    """Withdraw consent for a specific purpose"""
    try:
        consent_purpose = ConsentPurpose(purpose)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid purpose. Valid options: {[p.value for p in ConsentPurpose]}",
        )

    gdpr = get_gdpr()
    withdrawal = gdpr.withdraw_consent(user_id=user.id, purpose=consent_purpose)
    return {"success": True, "withdrawal": withdrawal.to_dict()}


@app.get("/gdpr/consent")
async def get_consent_status(
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
):
    """Get current consent status for all purposes"""
    gdpr = get_gdpr()
    history = gdpr.get_consent_history(user.id)
    current_status = {}
    for purpose in ConsentPurpose:
        current_status[purpose.value] = gdpr.check_consent(user.id, purpose)
    return {"consent_history": history, "current_status": current_status}


@app.get("/gdpr/data-export")
async def export_user_data(
    format: str = "json",
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
):
    """Export all user data (Right to Access / Data Portability)"""
    try:
        export_format = DataExportFormat(format)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Valid options: {[f.value for f in DataExportFormat]}",
        )

    gdpr = get_gdpr()
    request_obj = gdpr.request_data_access(user_id=user.id, format=export_format)
    exported = gdpr.export_user_data(user_id=user.id, format=export_format)
    return {
        "request_id": request_obj.request_id,
        "format": format,
        "data": exported,
    }


@app.post("/gdpr/deletion")
async def request_deletion(
    deletion_req: DeletionRequest,
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
):
    """Request data deletion (Right to Erasure) with 30-day grace period"""
    gdpr = get_gdpr()
    request_obj = gdpr.request_data_deletion(
        user_id=user.id, reason=deletion_req.reason
    )
    return {
        "success": True,
        "request": request_obj.to_dict(),
        "message": "Deletion request created with 30-day grace period. "
        "You may cancel this request during the grace period.",
    }


@app.delete("/gdpr/deletion/{request_id}")
async def cancel_deletion(
    request_id: str,
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
):
    """Cancel a pending deletion request during grace period"""
    gdpr = get_gdpr()
    success = gdpr.cancel_deletion_request(request_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel request. Either not found or no longer in grace period.",
        )
    return {"success": True, "message": "Deletion request cancelled."}


@app.put("/gdpr/rectify")
async def rectify_data(
    rectify_req: RectifyRequest,
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
):
    """Update incorrect personal data (Right to Rectification)"""
    gdpr = get_gdpr()
    result = gdpr.rectify_user_data(
        user_id=user.id, field=rectify_req.field, new_value=rectify_req.new_value
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Rectification failed"),
        )
    return result


@app.get("/gdpr/processing-activities")
async def get_processing_activities(
    user: User = Depends(require_auth),
    rate_limit_headers: dict = Depends(apply_rate_limit),
):
    """Get list of data processing activities"""
    gdpr = get_gdpr()
    activities = gdpr.get_processing_activities(user.id)
    return {"activities": activities}


if __name__ == "__main__":
    # Run the server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    print(f"Starting secure server on {host}:{port}")
    print("Security features enabled:")
    print(f"  - Authentication: {SECURITY_CONFIG.enable_authentication}")
    print(f"  - Rate limiting: {SECURITY_CONFIG.enable_rate_limiting}")
    print(f"  - Input validation: {SECURITY_CONFIG.enable_input_validation}")
    print(f"  - Audit logging: {SECURITY_CONFIG.enable_audit_logging}")

    uvicorn.run(
        "api_secure:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning",
    )
