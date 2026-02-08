"""
Pytest configuration and shared fixtures for tests.

This file provides common fixtures that can be used across all test files.
"""

import pytest
import sys
import os
import secrets

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import mock classes
from tests.mocks.models import (
    MockModel,
    MockCriticModel,
    MockJudgeModel,
    MockRuleGraph,
    MockMultiModalValidator,
    MockTenantManager,
)


@pytest.fixture
def mock_model():
    """Provide a mock model for testing"""
    return MockModel(model_name="test-model", temperature=0.0)


@pytest.fixture
def mock_critic_model():
    """Provide a mock critic model for testing"""
    return MockCriticModel(model_name="test-critic", temperature=0.0)


@pytest.fixture
def mock_judge_model():
    """Provide a mock judge model for testing"""
    return MockJudgeModel(model_name="test-judge", temperature=0.0)


@pytest.fixture
def mock_rule_graph():
    """Provide a mock rule graph for testing"""
    return MockRuleGraph()


@pytest.fixture
def mock_multimodal_validator():
    """Provide a mock multimodal validator for testing"""
    return MockMultiModalValidator()


@pytest.fixture
def mock_tenant_manager():
    """Provide a mock tenant manager for testing"""
    return MockTenantManager()


# ==================== Authentication Test Fixtures ====================
# Demo credentials for testing ONLY
# WARNING: These are INSECURE and must NEVER be used in production!
# They exist solely for automated testing purposes.

DEMO_PASSWORDS = {
    "admin": "password123",
    "api_client": "api_password123",
}


@pytest.fixture
def demo_passwords():
    """Provide demo passwords for testing"""
    return DEMO_PASSWORDS.copy()


@pytest.fixture
def mock_user_provider():
    """Provide a mock UserProvider for authentication testing"""
    try:
        from src.security.auth import (
            UserProvider,
            User,
            Role,
            ROLE_PERMISSIONS,
            hash_api_key,
            verify_api_key,
            generate_api_key,
        )
    except ImportError:
        # Skip if security module not available
        pytest.skip("Security module not available")
        return None

    class MockUserProvider(UserProvider):
        """Mock user provider for testing"""

        def __init__(self):
            self.users_db = {}
            self.passwords = DEMO_PASSWORDS.copy()
            self._initialize_default_users()

        def _initialize_default_users(self):
            """Initialize default test users"""
            admin_user = User(
                id="admin-001",
                username="admin",
                email="admin@example.com",
                role=Role.ADMIN,
                permissions=ROLE_PERMISSIONS[Role.ADMIN],
                is_active=True,
            )
            self.users_db[admin_user.username] = admin_user

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
            self.users_db[api_client.username] = api_client

        def get_user(self, username: str):
            return self.users_db.get(username)

        def authenticate_user(self, username: str, password: str):
            user = self.users_db.get(username)
            if not user or not user.is_active:
                return None

            # Verify password against demo passwords using constant-time comparison
            expected_password = self.passwords.get(username)
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

    return MockUserProvider()


@pytest.fixture(autouse=True)
def setup_auth_for_tests(mock_user_provider):
    """Automatically setup authentication for all tests"""
    try:
        from src.security.auth import set_user_provider
        
        # Set the mock user provider for tests
        if mock_user_provider:
            set_user_provider(mock_user_provider)
            
        yield
        
        # Cleanup after test
        # Reset to None to ensure clean state
        from src.security import auth
        auth._user_provider = None
    except ImportError:
        # Skip if security module not available
        yield
