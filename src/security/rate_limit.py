"""
Rate limiting and API key management
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib
import secrets
from dataclasses import dataclass, field
from enum import Enum

# Try to import redis as optional dependency
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

try:
    from fastapi import HTTPException, status
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    HTTPException = None
    status = None


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""

    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    window_size_seconds: int = 60  # For sliding window


@dataclass
class RateLimitRecord:
    """Rate limit record for a client"""

    requests: List[float] = field(default_factory=list)  # Timestamps of requests
    tokens: int = 0  # For token bucket strategy
    last_refill: float = field(default_factory=time.time)


class RateLimiter:
    """Rate limiter implementation"""

    def __init__(
        self,
        config: RateLimitConfig,
        use_redis: bool = False,
        redis_url: Optional[str] = None,
    ):
        self.config = config
        self.use_redis = use_redis
        self.redis_client = None

        if use_redis:
            if not REDIS_AVAILABLE:
                print("Warning: Redis requested but redis package not available")
                print("Install with: pip install -e \".[web]\" for redis support")
                print("Falling back to in-memory rate limiting")
                self.use_redis = False
            else:
                try:
                    self.redis_client = redis.Redis.from_url(
                        redis_url or "redis://localhost:6379"
                    )
                    self.redis_client.ping()
                except redis.ConnectionError:
                    self.use_redis = False
                    self.redis_client = None
                    print(
                        "Redis connection failed, falling back to in-memory rate limiting"
                    )
                except Exception as e:
                    self.use_redis = False
                    self.redis_client = None
                    print(f"Redis initialization failed: {e}, falling back to in-memory rate limiting")

        if not self.use_redis:
            self.records: Dict[str, RateLimitRecord] = {}

    def _get_redis_key(self, client_id: str, window: str) -> str:
        """Get Redis key for rate limiting"""
        return f"ratelimit:{client_id}:{window}"

    def check_rate_limit(
        self, client_id: str, endpoint: Optional[str] = None
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if client is within rate limits

        Returns:
            Tuple of (allowed, headers) where headers contain rate limit info
        """
        if self.use_redis:
            return self._check_rate_limit_redis(client_id, endpoint)
        else:
            return self._check_rate_limit_memory(client_id, endpoint)

    def _check_rate_limit_memory(
        self, client_id: str, endpoint: Optional[str] = None
    ) -> Tuple[bool, Dict[str, int]]:
        """Check rate limit using in-memory storage"""
        now = time.time()

        # Get or create record
        if client_id not in self.records:
            self.records[client_id] = RateLimitRecord(
                tokens=self.config.burst_limit, last_refill=now
            )

        record = self.records[client_id]

        # Clean old requests
        if self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            window_start = now - self.config.window_size_seconds
            record.requests = [ts for ts in record.requests if ts > window_start]

        # Check limits based on strategy
        if self.config.strategy == RateLimitStrategy.FIXED_WINDOW:
            # Fixed window: count requests in current minute
            current_minute = int(now // 60)
            minute_start = current_minute * 60

            requests_this_minute = sum(
                1 for ts in record.requests if ts >= minute_start
            )
            allowed = requests_this_minute < self.config.requests_per_minute

            # Calculate remaining requests
            remaining_minute = max(
                0, self.config.requests_per_minute - requests_this_minute
            )

            # For hourly and daily limits (simplified)
            hour_start = int(now // 3600) * 3600
            day_start = int(now // 86400) * 86400

            requests_this_hour = sum(1 for ts in record.requests if ts >= hour_start)
            requests_this_day = sum(1 for ts in record.requests if ts >= day_start)

            remaining_hour = max(0, self.config.requests_per_hour - requests_this_hour)
            remaining_day = max(0, self.config.requests_per_day - requests_this_day)

            remaining = min(remaining_minute, remaining_hour, remaining_day)

        elif self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            # Sliding window: count requests in sliding window
            window_start = now - self.config.window_size_seconds
            requests_in_window = sum(1 for ts in record.requests if ts >= window_start)

            allowed = requests_in_window < self.config.requests_per_minute
            remaining = max(0, self.config.requests_per_minute - requests_in_window)

        elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            # Token bucket: refill tokens over time
            time_passed = now - record.last_refill
            tokens_to_add = time_passed * (self.config.requests_per_minute / 60)

            record.tokens = min(self.config.burst_limit, record.tokens + tokens_to_add)
            record.last_refill = now

            if record.tokens >= 1:
                record.tokens -= 1
                allowed = True
                remaining = int(record.tokens)
            else:
                allowed = False
                remaining = 0

        else:
            allowed = True
            remaining = self.config.requests_per_minute

        # Add request timestamp
        if allowed:
            record.requests.append(now)
            # Keep only recent requests to save memory
            if len(record.requests) > 1000:
                record.requests = record.requests[-1000:]

        # Prepare headers
        headers = {
            "X-RateLimit-Limit": str(self.config.requests_per_minute),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(now // 60 + 1) * 60),  # Next minute
        }

        return allowed, headers

    def _check_rate_limit_redis(
        self, client_id: str, endpoint: Optional[str] = None
    ) -> Tuple[bool, Dict[str, int]]:
        """Check rate limit using Redis"""
        now = time.time()
        pipeline = self.redis_client.pipeline()

        # Minute window
        minute_key = self._get_redis_key(client_id, "minute")
        hour_key = self._get_redis_key(client_id, "hour")
        day_key = self._get_redis_key(client_id, "day")

        # Add current request
        pipeline.zadd(minute_key, {str(now): now})
        pipeline.zadd(hour_key, {str(now): now})
        pipeline.zadd(day_key, {str(now): now})

        # Remove old entries
        minute_ago = now - 60
        hour_ago = now - 3600
        day_ago = now - 86400

        pipeline.zremrangebyscore(minute_key, 0, minute_ago)
        pipeline.zremrangebyscore(hour_key, 0, hour_ago)
        pipeline.zremrangebyscore(day_key, 0, day_ago)

        # Get counts
        pipeline.zcard(minute_key)
        pipeline.zcard(hour_key)
        pipeline.zcard(day_key)

        # Set expiration
        pipeline.expire(minute_key, 120)
        pipeline.expire(hour_key, 7200)
        pipeline.expire(day_key, 172800)

        results = pipeline.execute()

        minute_count = results[3]
        hour_count = results[4]
        day_count = results[5]

        # Check limits
        minute_allowed = minute_count <= self.config.requests_per_minute
        hour_allowed = hour_count <= self.config.requests_per_hour
        day_allowed = day_count <= self.config.requests_per_day

        allowed = minute_allowed and hour_allowed and day_allowed

        # Calculate remaining
        remaining_minute = max(0, self.config.requests_per_minute - minute_count)
        remaining_hour = max(0, self.config.requests_per_hour - hour_count)
        remaining_day = max(0, self.config.requests_per_day - day_count)

        remaining = min(remaining_minute, remaining_hour, remaining_day)

        # Prepare headers
        headers = {
            "X-RateLimit-Limit": str(self.config.requests_per_minute),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(now // 60 + 1) * 60),
        }

        return allowed, headers


@dataclass
class APIKey:
    """API key information"""

    key: str
    key_hash: str
    name: str
    owner: str
    permissions: List[str]
    rate_limit_config: RateLimitConfig
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    is_active: bool = True
    expires_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        """Check if API key is valid"""
        if not self.is_active:
            return False

        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False

        return True

    def has_permission(self, permission: str) -> bool:
        """Check if API key has specific permission"""
        return permission in self.permissions


class APIKeyManager:
    """API key management"""

    def __init__(self, storage_backend: str = "memory"):
        self.storage_backend = storage_backend
        self.api_keys: Dict[str, APIKey] = {}  # key_hash -> APIKey

        # Initialize with default API key for testing
        self._initialize_default_keys()

    def _initialize_default_keys(self):
        """Initialize with default API keys for testing"""
        default_key = self.generate_api_key(
            name="Default API Key",
            owner="system",
            permissions=["api_execute", "api_read"],
            rate_limit_config=RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000,
            ),
        )
        print(f"Default API Key: {default_key.key}")
        print("Use this key for testing API access")

    def generate_api_key(
        self,
        name: str,
        owner: str,
        permissions: List[str],
        rate_limit_config: RateLimitConfig,
    ) -> APIKey:
        """Generate a new API key"""
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        api_key = APIKey(
            key=key,
            key_hash=key_hash,
            name=name,
            owner=owner,
            permissions=permissions,
            rate_limit_config=rate_limit_config,
        )

        self.api_keys[key_hash] = api_key
        return api_key

    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Validate API key and return key info if valid"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        if key_hash not in self.api_keys:
            return None

        api_key_info = self.api_keys[key_hash]

        if not api_key_info.is_valid():
            return None

        # Update last used timestamp
        api_key_info.last_used = datetime.utcnow()

        return api_key_info

    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        if key_hash not in self.api_keys:
            return False

        self.api_keys[key_hash].is_active = False
        return True

    def list_api_keys(self, owner: Optional[str] = None) -> List[APIKey]:
        """List API keys, optionally filtered by owner"""
        keys = list(self.api_keys.values())

        if owner:
            keys = [k for k in keys if k.owner == owner]

        # Don't expose the actual key, only the hash
        for key in keys:
            key.key = "[HIDDEN]"

        return keys

    def update_api_key_permissions(self, api_key: str, permissions: List[str]) -> bool:
        """Update API key permissions"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        if key_hash not in self.api_keys:
            return False

        self.api_keys[key_hash].permissions = permissions
        return True


# FastAPI dependencies for rate limiting
def check_rate_limit(
    rate_limiter: RateLimiter, client_id: str, endpoint: Optional[str] = None
):
    """FastAPI dependency for rate limiting"""
    if not FASTAPI_AVAILABLE:
        # If FastAPI is not available, just check and return headers
        allowed, headers = rate_limiter.check_rate_limit(client_id, endpoint)
        if not allowed:
            raise RuntimeError("Rate limit exceeded")
        return headers
    
    allowed, headers = rate_limiter.check_rate_limit(client_id, endpoint)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers=headers,
        )

    return headers


def validate_api_key(
    api_key_manager: APIKeyManager, api_key: Optional[str] = None
) -> Optional[APIKey]:
    """Validate API key and return key info"""
    if not api_key:
        return None

    return api_key_manager.validate_api_key(api_key)


# Default rate limiter instance
_default_rate_limiter = RateLimiter(RateLimitConfig())

# Default API key manager instance
_default_api_key_manager = APIKeyManager()
