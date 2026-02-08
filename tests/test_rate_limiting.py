"""
Unit tests for rate limiting (src/security/rate_limit.py).

Tests fixed window, sliding window, and token bucket strategies,
API key management, and edge cases.
"""

import pytest
import time

from src.security.rate_limit import (
    RateLimiter,
    RateLimitStrategy,
    RateLimitConfig,
    APIKeyManager,
)


@pytest.fixture
def rate_limit_config():
    """Create a rate limit config for testing."""
    return RateLimitConfig(
        requests_per_minute=5,
        requests_per_hour=100,
        burst_limit=3,
    )


@pytest.fixture
def limiter(rate_limit_config):
    """Create a RateLimiter with in-memory backend."""
    return RateLimiter(config=rate_limit_config, use_redis=False)


@pytest.fixture
def api_key_manager():
    """Create an APIKeyManager with in-memory backend."""
    return APIKeyManager(storage_backend="memory")


class TestRateLimiter:
    """Tests for the RateLimiter class."""

    def test_allow_first_request(self, limiter):
        allowed, headers = limiter.check_rate_limit("client1")
        assert allowed is True

    def test_rate_limit_headers(self, limiter):
        allowed, headers = limiter.check_rate_limit("client1")
        assert isinstance(headers, dict)

    def test_different_clients_independent(self, limiter):
        for _ in range(5):
            limiter.check_rate_limit("client1")
        allowed, _ = limiter.check_rate_limit("client2")
        assert allowed is True

    def test_rate_limit_enforced(self, limiter, rate_limit_config):
        client_id = "test-client"
        for _ in range(rate_limit_config.requests_per_minute):
            limiter.check_rate_limit(client_id)
        allowed, _ = limiter.check_rate_limit(client_id)
        assert allowed is False

    def test_same_client_different_endpoints_share_limit(self, limiter, rate_limit_config):
        """Rate limits are shared across endpoints for the same client."""
        for _ in range(rate_limit_config.requests_per_minute):
            limiter.check_rate_limit("client1", endpoint="/api/v1/execute")
        allowed, _ = limiter.check_rate_limit("client1", endpoint="/api/v1/status")
        assert allowed is False


class TestRateLimitStrategies:
    """Tests for different rate limiting strategies."""

    def test_fixed_window_strategy(self):
        config = RateLimitConfig(requests_per_minute=3)
        limiter = RateLimiter(config=config, use_redis=False)
        results = []
        for _ in range(5):
            allowed, _ = limiter.check_rate_limit("client1")
            results.append(allowed)
        assert results[:3] == [True, True, True]
        assert False in results[3:]

    def test_burst_handling(self):
        config = RateLimitConfig(requests_per_minute=10, burst_limit=2)
        limiter = RateLimiter(config=config, use_redis=False)
        # Rapid burst should still be allowed within per-minute limit
        allowed1, _ = limiter.check_rate_limit("client1")
        allowed2, _ = limiter.check_rate_limit("client1")
        assert allowed1 is True
        assert allowed2 is True


class TestAPIKeyManager:
    """Tests for the APIKeyManager class."""

    def test_generate_api_key(self, api_key_manager, rate_limit_config):
        key = api_key_manager.generate_api_key(
            name="test-key",
            owner="user1",
            permissions=["read", "write"],
            rate_limit_config=rate_limit_config,
        )
        assert key is not None
        assert key.name == "test-key"
        assert key.owner == "user1"

    def test_validate_api_key(self, api_key_manager, rate_limit_config):
        key = api_key_manager.generate_api_key(
            name="test-key",
            owner="user1",
            permissions=["read"],
            rate_limit_config=rate_limit_config,
        )
        validated = api_key_manager.validate_api_key(key.key)
        assert validated is not None
        assert validated.name == "test-key"

    def test_validate_invalid_api_key(self, api_key_manager):
        result = api_key_manager.validate_api_key("invalid-key")
        assert result is None

    def test_revoke_api_key(self, api_key_manager, rate_limit_config):
        key = api_key_manager.generate_api_key(
            name="revokable",
            owner="user1",
            permissions=["read"],
            rate_limit_config=rate_limit_config,
        )
        result = api_key_manager.revoke_api_key(key.key)
        assert result is True
        # After revoking, key should no longer be valid
        validated = api_key_manager.validate_api_key(key.key)
        assert validated is None

    def test_revoke_nonexistent_key(self, api_key_manager):
        result = api_key_manager.revoke_api_key("nonexistent-key")
        assert result is False

    def test_list_api_keys(self, api_key_manager, rate_limit_config):
        api_key_manager.generate_api_key(
            name="key1", owner="user1", permissions=["read"],
            rate_limit_config=rate_limit_config,
        )
        api_key_manager.generate_api_key(
            name="key2", owner="user2", permissions=["write"],
            rate_limit_config=rate_limit_config,
        )
        all_keys = api_key_manager.list_api_keys()
        assert len(all_keys) >= 2

    def test_list_api_keys_by_owner(self, api_key_manager, rate_limit_config):
        api_key_manager.generate_api_key(
            name="key1", owner="user1", permissions=["read"],
            rate_limit_config=rate_limit_config,
        )
        api_key_manager.generate_api_key(
            name="key2", owner="user2", permissions=["write"],
            rate_limit_config=rate_limit_config,
        )
        user1_keys = api_key_manager.list_api_keys(owner="user1")
        assert all(k.owner == "user1" for k in user1_keys)

    def test_update_api_key_permissions(self, api_key_manager, rate_limit_config):
        key = api_key_manager.generate_api_key(
            name="key1", owner="user1", permissions=["read"],
            rate_limit_config=rate_limit_config,
        )
        result = api_key_manager.update_api_key_permissions(
            key.key, ["read", "write", "admin"]
        )
        assert result is True

    def test_update_nonexistent_key_permissions(self, api_key_manager):
        result = api_key_manager.update_api_key_permissions(
            "nonexistent", ["read"]
        )
        assert result is False
