"""
Distributed State Manager for Multi-Instance Deployments

Provides:
- Cross-instance state synchronization via Redis
- Distributed locks for critical sections
- Session state management
- Instance coordination
"""

import time
import uuid
import json
import logging
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager

# Try to import redis as optional dependency
try:
    import redis
    from redis.exceptions import RedisError, LockError
    from redis.lock import Lock as RedisLock
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    RedisError = Exception
    LockError = Exception
    RedisLock = None

logger = logging.getLogger(__name__)


@dataclass
class DistributedStateConfig:
    """Configuration for distributed state manager"""
    
    enabled: bool = True
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 2  # Use separate DB from cache
    redis_password: Optional[str] = None
    key_prefix: str = "autonomai:state"
    lock_timeout: int = 30  # Lock timeout in seconds
    lock_blocking_timeout: int = 10  # How long to wait to acquire lock
    session_ttl: int = 3600  # Session TTL in seconds
    state_ttl: int = 86400  # State TTL in seconds (24 hours)
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30


class DistributedLock:
    """
    Distributed lock wrapper that provides thread-safe operations
    across multiple instances/processes.
    """
    
    def __init__(self, redis_lock: Optional[RedisLock], name: str, fallback: bool = False):
        self.redis_lock = redis_lock
        self.name = name
        self.fallback = fallback
        self._acquired = False
    
    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """Acquire the lock"""
        if self.fallback:
            # In fallback mode, always succeed (single instance)
            self._acquired = True
            return True
        
        if self.redis_lock:
            try:
                self._acquired = self.redis_lock.acquire(blocking=blocking, blocking_timeout=timeout)
                return self._acquired
            except Exception as e:
                logger.error(f"Error acquiring lock {self.name}: {e}")
                return False
        return False
    
    def release(self):
        """Release the lock"""
        if self.fallback:
            self._acquired = False
            return
        
        if self.redis_lock and self._acquired:
            try:
                self.redis_lock.release()
                self._acquired = False
            except Exception as e:
                logger.error(f"Error releasing lock {self.name}: {e}")
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class DistributedStateManager:
    """
    Manages distributed state and coordination across multiple instances.
    
    Features:
    - Distributed locks for critical sections
    - Cross-instance state synchronization
    - Session management
    - Instance registration and heartbeat
    """
    
    def __init__(self, config: DistributedStateConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.use_redis = False
        self.instance_id = str(uuid.uuid4())
        
        if config.enabled:
            self._initialize_redis()
        
        logger.info(
            f"DistributedStateManager initialized (Instance: {self.instance_id[:8]}, "
            f"Redis: {self.use_redis})"
        )
    
    def _initialize_redis(self):
        """Initialize Redis connection with error handling"""
        if not REDIS_AVAILABLE:
            logger.warning(
                "Redis package not available. Install with: pip install redis"
            )
            logger.warning("Running in single-instance mode without distributed coordination")
            return
        
        try:
            connection_params = {
                "decode_responses": True,  # Decode strings for easier handling
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
            
            # Register this instance
            self._register_instance()
            
            logger.info("Successfully connected to Redis for distributed state")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis for distributed state: {e}")
            logger.warning("Running in single-instance mode without distributed coordination")
            self.use_redis = False
            self.redis_client = None
    
    def _generate_key(self, key: str, namespace: str = "") -> str:
        """Generate a state key with prefix and namespace"""
        parts = [self.config.key_prefix]
        if namespace:
            parts.append(namespace)
        parts.append(key)
        return ":".join(parts)
    
    def _register_instance(self):
        """Register this instance in Redis"""
        if not self.use_redis or not self.redis_client:
            return
        
        try:
            key = self._generate_key(self.instance_id, "instances")
            data = {
                "instance_id": self.instance_id,
                "registered_at": datetime.utcnow().isoformat(),
                "last_heartbeat": datetime.utcnow().isoformat(),
            }
            self.redis_client.setex(
                key,
                self.config.session_ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Error registering instance: {e}")
    
    def heartbeat(self):
        """Update instance heartbeat"""
        if not self.use_redis or not self.redis_client:
            return
        
        try:
            key = self._generate_key(self.instance_id, "instances")
            data = self.redis_client.get(key)
            if data:
                instance_data = json.loads(data)
                instance_data["last_heartbeat"] = datetime.utcnow().isoformat()
                self.redis_client.setex(
                    key,
                    self.config.session_ttl,
                    json.dumps(instance_data)
                )
        except Exception as e:
            logger.error(f"Error updating heartbeat: {e}")
    
    def get_lock(self, resource: str, timeout: Optional[int] = None) -> DistributedLock:
        """
        Get a distributed lock for a resource.
        
        Args:
            resource: Resource name to lock (e.g., "instruction_update", "version_create")
            timeout: Lock timeout in seconds (None uses default)
        
        Returns:
            DistributedLock instance
        """
        timeout = timeout or self.config.lock_timeout
        lock_key = self._generate_key(resource, "locks")
        
        if not self.use_redis or not self.redis_client:
            # Fallback to no-op lock for single instance
            logger.debug(f"Using fallback lock for {resource} (single instance mode)")
            return DistributedLock(None, lock_key, fallback=True)
        
        try:
            redis_lock = self.redis_client.lock(
                lock_key,
                timeout=timeout,
                blocking_timeout=self.config.lock_blocking_timeout,
                thread_local=False  # Allow lock across threads
            )
            return DistributedLock(redis_lock, lock_key, fallback=False)
        except Exception as e:
            logger.error(f"Error creating lock for {resource}: {e}")
            # Fallback to no-op lock
            return DistributedLock(None, lock_key, fallback=True)
    
    @contextmanager
    def lock(self, resource: str, timeout: Optional[int] = None, blocking: bool = True):
        """
        Context manager for distributed locking.
        
        Usage:
            with state_manager.lock("my_resource", timeout=60):
                # Critical section
                pass
        """
        lock_timeout = timeout or self.config.lock_timeout
        lock = self.get_lock(resource, lock_timeout)
        acquired = lock.acquire(blocking=blocking, timeout=self.config.lock_blocking_timeout)
        
        if not acquired:
            raise LockError(f"Could not acquire lock for {resource}")
        
        try:
            yield lock
        finally:
            lock.release()
    
    def set_state(
        self,
        key: str,
        value: Any,
        namespace: str = "",
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set distributed state value.
        
        Args:
            key: State key
            value: Value to store (will be JSON serialized)
            namespace: Optional namespace
            ttl: Time-to-live in seconds (None uses default)
        
        Returns:
            True if successful
        """
        if not self.use_redis or not self.redis_client:
            return False
        
        full_key = self._generate_key(key, namespace)
        ttl = ttl or self.config.state_ttl
        
        try:
            serialized = json.dumps(value)
            self.redis_client.setex(full_key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting state {full_key}: {e}")
            return False
    
    def get_state(
        self,
        key: str,
        namespace: str = "",
        default: Any = None
    ) -> Any:
        """
        Get distributed state value.
        
        Args:
            key: State key
            namespace: Optional namespace
            default: Default value if not found
        
        Returns:
            Stored value or default
        """
        if not self.use_redis or not self.redis_client:
            return default
        
        full_key = self._generate_key(key, namespace)
        
        try:
            data = self.redis_client.get(full_key)
            if data is None:
                return default
            return json.loads(data)
        except Exception as e:
            logger.error(f"Error getting state {full_key}: {e}")
            return default
    
    def delete_state(self, key: str, namespace: str = "") -> bool:
        """Delete state value"""
        if not self.use_redis or not self.redis_client:
            return False
        
        full_key = self._generate_key(key, namespace)
        
        try:
            self.redis_client.delete(full_key)
            return True
        except Exception as e:
            logger.error(f"Error deleting state {full_key}: {e}")
            return False
    
    def increment(self, key: str, namespace: str = "", amount: int = 1) -> Optional[int]:
        """
        Atomically increment a counter.
        
        Args:
            key: Counter key
            namespace: Optional namespace
            amount: Amount to increment by
        
        Returns:
            New value or None on error
        """
        if not self.use_redis or not self.redis_client:
            return None
        
        full_key = self._generate_key(key, namespace)
        
        try:
            return self.redis_client.incrby(full_key, amount)
        except Exception as e:
            logger.error(f"Error incrementing {full_key}: {e}")
            return None
    
    def get_active_instances(self) -> List[Dict[str, Any]]:
        """
        Get list of active instances.
        
        Returns:
            List of instance data dictionaries
        """
        if not self.use_redis or not self.redis_client:
            return [{"instance_id": self.instance_id, "status": "single_instance"}]
        
        try:
            pattern = self._generate_key("*", "instances")
            keys = self.redis_client.keys(pattern)
            instances = []
            
            for key in keys:
                data = self.redis_client.get(key)
                if data:
                    instances.append(json.loads(data))
            
            return instances
        except Exception as e:
            logger.error(f"Error getting active instances: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.
        
        Returns:
            Health status dictionary
        """
        health = {
            "instance_id": self.instance_id,
            "distributed_mode": self.use_redis,
            "redis_available": REDIS_AVAILABLE,
            "healthy": True,
        }
        
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.ping()
                active_instances = self.get_active_instances()
                health["active_instances"] = len(active_instances)
                health["instances"] = active_instances
            except Exception as e:
                health["healthy"] = False
                health["error"] = str(e)
        
        return health
    
    def close(self):
        """Close connections and cleanup"""
        if self.redis_client:
            try:
                # Remove instance registration
                key = self._generate_key(self.instance_id, "instances")
                self.redis_client.delete(key)
                self.redis_client.close()
            except Exception as e:
                logger.error(f"Error closing distributed state manager: {e}")
