"""
Unit tests for authentication system (src/security/auth.py).

Tests JWT token creation/verification, role-based access control,
API key management, user permissions, and edge cases.
"""

import pytest
import time
from datetime import timedelta

from src.security.auth import (
    Role,
    Permission,
    ROLE_PERMISSIONS,
    User,
    Token,
    TokenData,
    UserProvider,
    generate_api_key,
    hash_api_key,
    verify_api_key,
    create_access_token,
    create_refresh_token,
    verify_token,
    set_user_provider,
    get_user_provider,
    authenticate_user,
    authenticate_with_api_key,
    get_user,
    create_user,
)
from fastapi import HTTPException


class TestRolesAndPermissions:
    """Tests for role and permission definitions."""

    def test_all_roles_have_permissions(self):
        for role in Role:
            assert role in ROLE_PERMISSIONS

    def test_admin_has_all_permissions(self):
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
        for perm in Permission:
            assert perm in admin_perms

    def test_viewer_cannot_edit(self):
        viewer_perms = ROLE_PERMISSIONS[Role.VIEWER]
        assert Permission.EDIT_INSTRUCTIONS not in viewer_perms
        assert Permission.MANAGE_USERS not in viewer_perms

    def test_api_client_limited_permissions(self):
        api_perms = ROLE_PERMISSIONS[Role.API_CLIENT]
        assert Permission.API_EXECUTE in api_perms
        assert Permission.API_READ in api_perms
        assert Permission.MANAGE_SYSTEM not in api_perms


class TestUserModel:
    """Tests for User model."""

    def test_user_has_permission(self):
        user = User(
            id="u1",
            username="test",
            email="test@test.com",
            role=Role.ADMIN,
            permissions=[Permission.EXECUTE_QUERY, Permission.VIEW_INSTRUCTIONS],
        )
        assert user.has_permission(Permission.EXECUTE_QUERY) is True
        assert user.has_permission(Permission.MANAGE_USERS) is False

    def test_user_can_access(self):
        user = User(
            id="u1",
            username="test",
            email="test@test.com",
            role=Role.EDITOR,
            permissions=[Permission.EXECUTE_QUERY, Permission.VIEW_INSTRUCTIONS],
        )
        assert user.can_access([Permission.EXECUTE_QUERY]) is True
        assert user.can_access([Permission.EXECUTE_QUERY, Permission.MANAGE_USERS]) is False

    def test_user_default_active(self):
        user = User(
            id="u1",
            username="test",
            email="test@test.com",
            role=Role.VIEWER,
        )
        assert user.is_active is True


class TestAPIKeyManagement:
    """Tests for API key generation, hashing, and verification."""

    def test_generate_api_key_returns_string(self):
        key = generate_api_key()
        assert isinstance(key, str)
        assert len(key) > 20

    def test_generate_api_key_unique(self):
        keys = {generate_api_key() for _ in range(10)}
        assert len(keys) == 10

    def test_hash_api_key(self):
        key = "test_api_key_12345"
        hashed = hash_api_key(key)
        assert hashed != key
        assert len(hashed) == 64  # SHA-256 hex digest

    def test_verify_api_key_correct(self):
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert verify_api_key(key, hashed) is True

    def test_verify_api_key_incorrect(self):
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert verify_api_key("wrong_key", hashed) is False


class TestJWTTokens:
    """Tests for JWT token creation and verification."""

    def test_create_access_token(self):
        token = create_access_token(
            data={
                "sub": "admin",
                "user_id": "u1",
                "role": "admin",
                "permissions": ["execute_query"],
            }
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        token = create_access_token(
            data={
                "sub": "admin",
                "user_id": "u1",
                "role": "admin",
                "permissions": ["execute_query"],
            }
        )
        token_data = verify_token(token)
        assert token_data.username == "admin"
        assert token_data.user_id == "u1"
        assert token_data.role == Role.ADMIN

    def test_verify_expired_token(self):
        token = create_access_token(
            data={
                "sub": "admin",
                "user_id": "u1",
                "role": "admin",
                "permissions": [],
            },
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401

    def test_verify_invalid_token(self):
        with pytest.raises((HTTPException, AttributeError)):
            verify_token("invalid.jwt.token")

    def test_create_refresh_token(self):
        token = create_refresh_token(
            data={
                "sub": "admin",
                "user_id": "u1",
                "role": "admin",
                "permissions": [],
            }
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_with_custom_expiry(self):
        token = create_access_token(
            data={
                "sub": "user",
                "user_id": "u2",
                "role": "viewer",
                "permissions": ["api_read"],
            },
            expires_delta=timedelta(hours=1),
        )
        token_data = verify_token(token)
        assert token_data.username == "user"

    def test_token_without_username_raises(self):
        token = create_access_token(
            data={
                "user_id": "u1",
                "role": "admin",
                "permissions": [],
            }
        )
        with pytest.raises((HTTPException, AttributeError)):
            verify_token(token)


class TestUserProvider:
    """Tests for user provider interface and authentication functions."""

    def test_get_user_provider_not_set_raises(self):
        from src.security import auth

        old = auth._user_provider
        auth._user_provider = None
        try:
            with pytest.raises(RuntimeError):
                get_user_provider()
        finally:
            auth._user_provider = old

    def test_set_user_provider(self, mock_user_provider):
        set_user_provider(mock_user_provider)
        provider = get_user_provider()
        assert provider is mock_user_provider

    def test_authenticate_user_valid(self, mock_user_provider):
        set_user_provider(mock_user_provider)
        user = authenticate_user("admin", "password123")
        assert user is not None
        assert user.username == "admin"

    def test_authenticate_user_invalid_password(self, mock_user_provider):
        set_user_provider(mock_user_provider)
        user = authenticate_user("admin", "wrong_password")
        assert user is None

    def test_authenticate_user_unknown_user(self, mock_user_provider):
        set_user_provider(mock_user_provider)
        user = authenticate_user("unknown_user", "password123")
        assert user is None

    def test_get_user_none_username(self, mock_user_provider):
        set_user_provider(mock_user_provider)
        user = get_user(None)
        assert user is None

    def test_get_user_existing(self, mock_user_provider):
        set_user_provider(mock_user_provider)
        user = get_user("admin")
        assert user is not None
        assert user.role == Role.ADMIN

    def test_create_user(self, mock_user_provider):
        set_user_provider(mock_user_provider)
        user = create_user("newuser", "new@test.com", Role.VIEWER)
        assert user.username == "newuser"
        assert user.role == Role.VIEWER

    def test_create_duplicate_user_raises(self, mock_user_provider):
        set_user_provider(mock_user_provider)
        with pytest.raises(ValueError):
            create_user("admin", "admin@test.com", Role.ADMIN)


class TestTokenModel:
    """Tests for Token and TokenData models."""

    def test_token_model(self):
        token = Token(
            access_token="access",
            refresh_token="refresh",
        )
        assert token.token_type == "bearer"
        assert token.expires_in > 0

    def test_token_data_model(self):
        data = TokenData(
            username="user",
            user_id="u1",
            role=Role.EDITOR,
            permissions=[Permission.EXECUTE_QUERY],
        )
        assert data.username == "user"
        assert data.role == Role.EDITOR
