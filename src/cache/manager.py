"""
Core cache manager with Redis backend and multiple invalidation strategies.
"""

import time
import hashlib
import json
import pickle
from typing import Any, Optional, Dict, List, Callable
from enum import Enum
from dataclasses import dataclass, field
import logging

# Try to import redis as optional dependency
try:
    import redis
    from redis.exceptions import RedisError

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    RedisError = Exception

logger = logging.getLogger(__name__)


class CacheStrategy(str, Enum):
    """Cache invalidation strategies"""

    TTL = "ttl"  # Time-to-live based expiration
    LRU = "lru"  # Least recently used
    LFU = "lfu"  # Least frequently used
    MANUAL = "manual"  # Manual invalidation only


@dataclass
class CacheConfig:
    """Configuration for cache manager"""

    enabled: bool = True
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_password: Optional[str] = None
    default_ttl: int = 3600  # 1 hour default TTL in seconds
    max_memory_mb: int = 512  # Max memory for Redis in MB
    eviction_policy: str = "allkeys-lru"  # Redis eviction policy
    strategy: CacheStrategy = CacheStrategy.TTL
    key_prefix: str = "autonomai"
    enable_compression: bool = False
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30  # seconds


class CacheManager:
    """
    Distributed cache manager using Redis with support for multiple
    invalidation strategies and failover to in-memory cache.
    """

    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, tuple] = {}  # key -> (value, timestamp, access_count)
        self.use_redis = False

        if config.enabled:
            self._initialize_redis()

        logger.info(
            f"CacheManager initialized (Redis: {self.use_redis}, "
            f"Strategy: {config.strategy})"
        )

    def _initialize_redis(self):
        """Initialize Redis connection with error handling"""
        if not REDIS_AVAILABLE:
            logger.warning(
                "Redis package not available. Install with: pip install redis"
            )
            logger.warning("Falling back to in-memory caching")
            return

        try:
            # Parse Redis URL or construct connection parameters
            connection_params = {
                "decode_responses": False,  # We'll handle encoding
                "socket_timeout": self.config.socket_timeout,
                "socket_connect_timeout": self.config.socket_connect_timeout,
                "retry_on_timeout": self.config.retry_on_timeout,
                "health_check_interval": self.config.health_check_interval,
            }

            if self.config.redis_password:
                connection_params["password"] = self.config.redis_password

            self.redis_client = redis.Redis.from_url(
                self.config.redis_url,
                db=self.config.redis_db,
                **connection_params,
            )

            # Test connection
            self.redis_client.ping()
            self.use_redis = True

            # Configure Redis memory policy if possible
            try:
                self.redis_client.config_set("maxmemory-policy", self.config.eviction_policy)
                logger.info(f"Redis eviction policy set to: {self.config.eviction_policy}")
            except Exception as e:
                logger.warning(f"Could not set Redis eviction policy: {e}")

            logger.info("Successfully connected to Redis")

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            logger.warning("Falling back to in-memory caching")
            self.use_redis = False
            self.redis_client = None

    def _generate_key(self, key: str, namespace: str = "") -> str:
        """Generate a cache key with prefix and namespace"""
        parts = [self.config.key_prefix]
        if namespace:
            parts.append(namespace)
        parts.append(key)
        return ":".join(parts)

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Use pickle for Python objects
            return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise

    def get(
        self, key: str, namespace: str = "", default: Any = None
    ) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key
            namespace: Optional namespace for key organization
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        if not self.config.enabled:
            return default

        full_key = self._generate_key(key, namespace)

        try:
            if self.use_redis and self.redis_client:
                return self._get_redis(full_key, default)
            else:
                return self._get_memory(full_key, default)
        except Exception as e:
            logger.error(f"Cache get error for key {full_key}: {e}")
            return default

    def _get_redis(self, key: str, default: Any = None) -> Optional[Any]:
        """Get value from Redis"""
        try:
            data = self.redis_client.get(key)
            if data is None:
                return default

            # Update access count for LFU strategy
            if self.config.strategy == CacheStrategy.LFU:
                self.redis_client.incr(f"{key}:access_count")

            return self._deserialize(data)
        except RedisError as e:
            logger.error(f"Redis get error: {e}")
            # Fallback to memory cache
            return self._get_memory(key, default)

    def _get_memory(self, key: str, default: Any = None) -> Optional[Any]:
        """Get value from in-memory cache"""
        if key not in self.memory_cache:
            return default

        value, timestamp, access_count = self.memory_cache[key]

        # Check TTL if using TTL strategy
        if self.config.strategy == CacheStrategy.TTL:
            if time.time() - timestamp > self.config.default_ttl:
                del self.memory_cache[key]
                return default

        # Update access count for LFU
        if self.config.strategy == CacheStrategy.LFU:
            self.memory_cache[key] = (value, timestamp, access_count + 1)

        return value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "",
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None uses default)
            namespace: Optional namespace for key organization

        Returns:
            True if successful, False otherwise
        """
        if not self.config.enabled:
            return False

        full_key = self._generate_key(key, namespace)
        ttl = ttl if ttl is not None else self.config.default_ttl

        try:
            if self.use_redis and self.redis_client:
                return self._set_redis(full_key, value, ttl)
            else:
                return self._set_memory(full_key, value, ttl)
        except Exception as e:
            logger.error(f"Cache set error for key {full_key}: {e}")
            return False

    def _set_redis(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in Redis"""
        try:
            data = self._serialize(value)

            if self.config.strategy == CacheStrategy.TTL:
                # Use SETEX for TTL
                self.redis_client.setex(key, ttl, data)
            else:
                # Use SET for other strategies
                self.redis_client.set(key, data)
                if self.config.strategy == CacheStrategy.LFU:
                    self.redis_client.set(f"{key}:access_count", 0)

            return True
        except RedisError as e:
            logger.error(f"Redis set error: {e}")
            # Fallback to memory cache
            return self._set_memory(key, value, ttl)

    def _set_memory(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in in-memory cache"""
        self.memory_cache[key] = (value, time.time(), 0)

        # Implement simple LRU eviction if cache gets too large
        if len(self.memory_cache) > 10000:
            # Remove 10% of oldest entries
            sorted_keys = sorted(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k][1],
            )
            for k in sorted_keys[:1000]:
                del self.memory_cache[k]

        return True

    def delete(self, key: str, namespace: str = "") -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key
            namespace: Optional namespace

        Returns:
            True if successful
        """
        if not self.config.enabled:
            return False

        full_key = self._generate_key(key, namespace)

        try:
            if self.use_redis and self.redis_client:
                self.redis_client.delete(full_key)
                if self.config.strategy == CacheStrategy.LFU:
                    self.redis_client.delete(f"{full_key}:access_count")
            else:
                if full_key in self.memory_cache:
                    del self.memory_cache[full_key]
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {full_key}: {e}")
            return False

    def clear(self, namespace: str = "") -> bool:
        """
        Clear all keys in namespace (or all keys if no namespace)

        Args:
            namespace: Optional namespace to clear

        Returns:
            True if successful
        """
        if not self.config.enabled:
            return False

        try:
            if self.use_redis and self.redis_client:
                pattern = self._generate_key("*", namespace)
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                if namespace:
                    prefix = self._generate_key("", namespace)
                    keys_to_delete = [
                        k for k in self.memory_cache.keys() if k.startswith(prefix)
                    ]
                    for k in keys_to_delete:
                        del self.memory_cache[k]
                else:
                    self.memory_cache.clear()
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def exists(self, key: str, namespace: str = "") -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key
            namespace: Optional namespace

        Returns:
            True if key exists
        """
        if not self.config.enabled:
            return False

        full_key = self._generate_key(key, namespace)

        try:
            if self.use_redis and self.redis_client:
                return bool(self.redis_client.exists(full_key))
            else:
                return full_key in self.memory_cache
        except Exception as e:
            logger.error(f"Cache exists error for key {full_key}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        stats = {
            "enabled": self.config.enabled,
            "backend": "redis" if self.use_redis else "memory",
            "strategy": self.config.strategy,
        }

        try:
            if self.use_redis and self.redis_client:
                info = self.redis_client.info("stats")
                stats.update(
                    {
                        "total_connections": info.get("total_connections_received", 0),
                        "total_commands": info.get("total_commands_processed", 0),
                        "keyspace_hits": info.get("keyspace_hits", 0),
                        "keyspace_misses": info.get("keyspace_misses", 0),
                        "used_memory_mb": info.get("used_memory", 0) / 1024 / 1024,
                    }
                )

                # Calculate hit rate
                hits = info.get("keyspace_hits", 0)
                misses = info.get("keyspace_misses", 0)
                total = hits + misses
                stats["hit_rate"] = (hits / total * 100) if total > 0 else 0

            else:
                stats.update(
                    {
                        "memory_keys": len(self.memory_cache),
                    }
                )
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            stats["error"] = str(e)

        return stats

    def health_check(self) -> bool:
        """
        Check if cache is healthy

        Returns:
            True if cache is operational
        """
        if not self.config.enabled:
            return True

        try:
            if self.use_redis and self.redis_client:
                self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False

    def close(self):
        """Close cache connections"""
        if self.redis_client:
            try:
                self.redis_client.close()
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
