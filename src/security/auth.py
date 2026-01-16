"""
Authentication and authorization system for the Self-Optimizing Instruction Library
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from enum import Enum
import hashlib
import secrets
import jwt
from pydantic import BaseModel, Field
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Security configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Should be in environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class Role(str, Enum):
    """User roles with different permission levels"""

    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    API_CLIENT = "api_client"


class Permission(str, Enum):
    """Available permissions"""

    # System permissions
    EXECUTE_QUERY = "execute_query"
    VIEW_INSTRUCTIONS = "view_instructions"
    EDIT_INSTRUCTIONS = "edit_instructions"
    MANAGE_USERS = "manage_users"
    VIEW_METRICS = "view_metrics"
    MANAGE_SYSTEM = "manage_system"

    # API permissions
    API_EXECUTE = "api_execute"
    API_READ = "api_read"
    API_WRITE = "api_write"


# Role to permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.EXECUTE_QUERY,
        Permission.VIEW_INSTRUCTIONS,
        Permission.EDIT_INSTRUCTIONS,
        Permission.MANAGE_USERS,
        Permission.VIEW_METRICS,
        Permission.MANAGE_SYSTEM,
        Permission.API_EXECUTE,
        Permission.API_READ,
        Permission.API_WRITE,
    ],
    Role.EDITOR: [
        Permission.EXECUTE_QUERY,
        Permission.VIEW_INSTRUCTIONS,
        Permission.EDIT_INSTRUCTIONS,
        Permission.VIEW_METRICS,
        Permission.API_EXECUTE,
        Permission.API_READ,
    ],
    Role.VIEWER: [
        Permission.EXECUTE_QUERY,
        Permission.VIEW_INSTRUCTIONS,
        Permission.VIEW_METRICS,
        Permission.API_EXECUTE,
        Permission.API_READ,
    ],
    Role.API_CLIENT: [
        Permission.API_EXECUTE,
        Permission.API_READ,
    ],
}


class User(BaseModel):
    """User model for authentication"""

    id: str
    username: str
    email: str
    role: Role
    permissions: List[Permission] = Field(default_factory=list)
    api_key: Optional[str] = None
    api_key_hash: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions

    def can_access(self, required_permissions: List[Permission]) -> bool:
        """Check if user has all required permissions"""
        return all(perm in self.permissions for perm in required_permissions)


class Token(BaseModel):
    """JWT token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


class TokenData(BaseModel):
    """Token payload data"""

    username: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[Role] = None
    permissions: List[Permission] = Field(default_factory=list)


# Mock user database (in production, use a real database)
_users_db: Dict[str, User] = {}

# Demo passwords (in production, use proper password hashing)
_demo_passwords: Dict[str, str] = {
    "admin": "password123",
    "api_client": "api_password123",
}


# Initialize with default admin user
def _initialize_default_users():
    """Initialize default users for testing"""
    admin_user = User(
        id="admin-001",
        username="admin",
        email="admin@example.com",
        role=Role.ADMIN,
        permissions=ROLE_PERMISSIONS[Role.ADMIN],
        is_active=True,
    )
    _users_db[admin_user.username] = admin_user

    # Create API client user
    api_key = generate_api_key()
    api_client = User(
        id="api-001",
        username="api_client",
        email="api@example.com",
        role=Role.API_CLIENT,
        permissions=ROLE_PERMISSIONS[Role.API_CLIENT],
        api_key=api_key,
        api_key_hash=hash_api_key(api_key),
        is_active=True,
    )
    _users_db[api_client.username] = api_client


def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, api_key_hash: str) -> bool:
    """Verify API key against hash"""
    return hash_api_key(api_key) == api_key_hash


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify JWT token and return token data"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        role: Role = Role(payload.get("role"))
        permissions: List[Permission] = [
            Permission(p) for p in payload.get("permissions", [])
        ]

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        return TokenData(
            username=username,
            user_id=user_id,
            role=role,
            permissions=permissions,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    # In production, use proper password hashing and database lookup
    user = _users_db.get(username)
    if not user or not user.is_active:
        return None

    # Verify password against demo passwords
    expected_password = _demo_passwords.get(username)
    if expected_password and password == expected_password:
        return user
    return None


def authenticate_with_api_key(api_key: str) -> Optional[User]:
    """Authenticate user with API key"""
    for user in _users_db.values():
        if user.api_key_hash and verify_api_key(api_key, user.api_key_hash):
            return user
    return None


def get_user(username: Optional[str]) -> Optional[User]:
    """Get user by username"""
    if username is None:
        return None
    return _users_db.get(username)


def create_user(username: str, email: str, role: Role) -> User:
    """Create new user"""
    if username in _users_db:
        raise ValueError(f"User {username} already exists")

    user = User(
        id=f"user-{len(_users_db) + 1:03d}",
        username=username,
        email=email,
        role=role,
        permissions=ROLE_PERMISSIONS[role],
        is_active=True,
    )
    _users_db[username] = user
    return user


# FastAPI dependencies
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """FastAPI dependency to get current authenticated user"""
    token = credentials.credentials
    token_data = verify_token(token)

    user = get_user(token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_user_or_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """Get current user or authenticate with API key from header"""
    if not credentials:
        # Check for API key in custom header
        # This would be implemented in the actual API endpoint
        return None

    token = credentials.credentials

    # Check if it's an API key (starts with sk_)
    if token.startswith("sk_"):
        user = authenticate_with_api_key(token)
        if user:
            return user

    # Otherwise, treat as JWT token
    try:
        token_data = verify_token(token)
        user = get_user(token_data.username)
        return user
    except HTTPException:
        return None


def require_permission(permission: Permission):
    """Decorator to require specific permission"""

    def permission_dependency(current_user: User = Depends(get_current_user)):
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission {permission.value} required",
            )
        return current_user

    return permission_dependency


def require_role(role: Role):
    """Decorator to require specific role"""

    def role_dependency(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {role.value} required",
            )
        return current_user

    return role_dependency


# Initialize default users
_initialize_default_users()
