"""
Tests for Distributed State Management

Tests distributed locks, state synchronization, and multi-instance coordination.
"""

import pytest
import time
import threading
from pathlib import Path
from src.storage.distributed_state import (
    DistributedStateManager,
    DistributedStateConfig,
    DistributedLock,
    REDIS_AVAILABLE
)


@pytest.fixture
def state_config():
    """Create test state configuration"""
    return DistributedStateConfig(
        enabled=True,
        redis_url="redis://localhost:6379",
        redis_db=3,  # Use separate DB for testing
        key_prefix="test:autonomai:state",
        lock_timeout=5,
        lock_blocking_timeout=2,
    )


@pytest.fixture
def state_manager(state_config):
    """Create state manager instance"""
    manager = DistributedStateManager(state_config)
    yield manager
    # Cleanup
    if manager.use_redis and manager.redis_client:
        # Clear test keys
        pattern = state_config.key_prefix + ":*"
        keys = manager.redis_client.keys(pattern)
        if keys:
            manager.redis_client.delete(*keys)
    manager.close()


class TestDistributedStateManager:
    """Test distributed state manager"""
    
    def test_initialization(self, state_manager):
        """Test manager initialization"""
        assert state_manager is not None
        assert state_manager.instance_id is not None
        
        # Check if Redis is available
        if REDIS_AVAILABLE:
            # Should attempt Redis connection
            pass
        else:
            # Should fallback to single instance mode
            assert not state_manager.use_redis
    
    def test_health_check(self, state_manager):
        """Test health check"""
        health = state_manager.health_check()
        
        assert "instance_id" in health
        assert "distributed_mode" in health
        assert "healthy" in health
        assert health["instance_id"] == state_manager.instance_id
    
    def test_set_get_state(self, state_manager):
        """Test state storage and retrieval"""
        if not state_manager.use_redis:
            pytest.skip("Redis not available")
        
        # Set state
        success = state_manager.set_state(
            "test_key",
            {"value": "test_data", "count": 42},
            namespace="test"
        )
        assert success
        
        # Get state
        value = state_manager.get_state("test_key", namespace="test")
        assert value == {"value": "test_data", "count": 42}
        
        # Get non-existent key
        value = state_manager.get_state("nonexistent", default="default_value")
        assert value == "default_value"
    
    def test_delete_state(self, state_manager):
        """Test state deletion"""
        if not state_manager.use_redis:
            pytest.skip("Redis not available")
        
        # Set and delete
        state_manager.set_state("temp_key", "temp_value")
        success = state_manager.delete_state("temp_key")
        assert success
        
        # Verify deleted
        value = state_manager.get_state("temp_key")
        assert value is None
    
    def test_increment_counter(self, state_manager):
        """Test atomic counter increment"""
        if not state_manager.use_redis:
            pytest.skip("Redis not available")
        
        # Increment counter
        value1 = state_manager.increment("counter", namespace="test")
        value2 = state_manager.increment("counter", namespace="test")
        value3 = state_manager.increment("counter", namespace="test", amount=5)
        
        assert value1 == 1
        assert value2 == 2
        assert value3 == 7
    
    def test_distributed_lock_basic(self, state_manager):
        """Test basic distributed lock functionality"""
        if not state_manager.use_redis:
            pytest.skip("Redis not available")
        
        # Get lock
        lock = state_manager.get_lock("test_resource")
        assert lock is not None
        
        # Acquire lock
        acquired = lock.acquire(blocking=False)
        assert acquired
        
        # Release lock
        lock.release()
    
    def test_distributed_lock_context_manager(self, state_manager):
        """Test lock with context manager"""
        if not state_manager.use_redis:
            pytest.skip("Redis not available")
        
        # Use lock as context manager
        with state_manager.lock("test_resource_cm"):
            # Lock should be held here
            # Try to acquire same lock from different thread (should fail)
            lock2 = state_manager.get_lock("test_resource_cm")
            acquired = lock2.acquire(blocking=False)
            assert not acquired
    
    def test_distributed_lock_timeout(self, state_manager):
        """Test lock timeout"""
        if not state_manager.use_redis:
            pytest.skip("Redis not available")
        
        # Acquire lock with short timeout
        lock1 = state_manager.get_lock("timeout_test", timeout=1)
        lock1.acquire()
        
        # Wait for timeout
        time.sleep(2)
        
        # Should be able to acquire now (lock expired)
        lock2 = state_manager.get_lock("timeout_test", timeout=1)
        acquired = lock2.acquire(blocking=False)
        assert acquired
        lock2.release()
    
    def test_concurrent_lock_access(self, state_manager):
        """Test that locks prevent concurrent access"""
        if not state_manager.use_redis:
            pytest.skip("Redis not available")
        
        results = {"count": 0, "conflicts": 0}
        
        def increment_with_lock():
            """Increment counter with lock protection"""
            try:
                with state_manager.lock("increment_lock", timeout=5):
                    # Critical section
                    current = results["count"]
                    time.sleep(0.01)  # Simulate work
                    results["count"] = current + 1
            except Exception as e:
                results["conflicts"] += 1
        
        # Run multiple threads concurrently
        threads = []
        for _ in range(10):
            t = threading.Thread(target=increment_with_lock)
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # All increments should succeed without conflicts
        assert results["count"] == 10
        assert results["conflicts"] == 0
    
    def test_concurrent_access_without_lock(self, state_manager):
        """Test that concurrent access without locks can cause issues"""
        if not state_manager.use_redis:
            pytest.skip("Redis not available")
        
        results = {"count": 0}
        
        def increment_without_lock():
            """Increment counter WITHOUT lock protection"""
            current = results["count"]
            time.sleep(0.01)  # Simulate work
            results["count"] = current + 1
        
        # Run multiple threads concurrently
        threads = []
        for _ in range(10):
            t = threading.Thread(target=increment_without_lock)
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Due to race conditions, count will likely be < 10
        # This demonstrates why locks are necessary
        # Note: This test may occasionally pass if timing is lucky
        # but will usually fail
        print(f"Without lock: count = {results['count']} (expected 10)")
    
    def test_active_instances_tracking(self, state_manager):
        """Test instance registration and tracking"""
        if not state_manager.use_redis:
            pytest.skip("Redis not available")
        
        # Get active instances
        instances = state_manager.get_active_instances()
        assert isinstance(instances, list)
        
        # Should include at least this instance
        instance_ids = [i["instance_id"] for i in instances]
        assert state_manager.instance_id in instance_ids
    
    def test_heartbeat(self, state_manager):
        """Test instance heartbeat"""
        if not state_manager.use_redis:
            pytest.skip("Redis not available")
        
        # Initial registration
        instances_before = state_manager.get_active_instances()
        
        # Send heartbeat
        state_manager.heartbeat()
        
        # Should still be registered
        instances_after = state_manager.get_active_instances()
        assert len(instances_after) >= len(instances_before)
    
    def test_fallback_mode(self):
        """Test fallback to single-instance mode"""
        # Create config with invalid Redis URL
        config = DistributedStateConfig(
            enabled=True,
            redis_url="redis://invalid-host:6379",
            redis_db=3,
        )
        
        manager = DistributedStateManager(config)
        
        # Should fallback to single instance mode
        # Even if Redis is available as a package, connection should fail
        assert not manager.use_redis
        
        # Locks should still work (as no-ops)
        lock = manager.get_lock("test_resource")
        assert lock.fallback
        
        acquired = lock.acquire()
        assert acquired
        lock.release()
        
        manager.close()


class TestDistributedLock:
    """Test distributed lock implementation"""
    
    def test_fallback_lock(self):
        """Test fallback lock behavior"""
        lock = DistributedLock(None, "test", fallback=True)
        
        # Should always acquire
        assert lock.acquire()
        assert lock._acquired
        
        # Release should work
        lock.release()
        assert not lock._acquired
    
    def test_lock_context_manager(self):
        """Test lock as context manager"""
        lock = DistributedLock(None, "test", fallback=True)
        
        with lock:
            assert lock._acquired
        
        assert not lock._acquired


class TestMultiInstanceScenarios:
    """Test scenarios with multiple instances"""
    
    def test_two_instances_communication(self, state_config):
        """Test two instances sharing state"""
        if not REDIS_AVAILABLE:
            pytest.skip("Redis not available")
        
        # Create two manager instances
        manager1 = DistributedStateManager(state_config)
        manager2 = DistributedStateManager(state_config)
        
        if not manager1.use_redis or not manager2.use_redis:
            pytest.skip("Redis connection failed")
        
        try:
            # Manager 1 sets state
            manager1.set_state("shared_key", {"from": "manager1"})
            
            # Manager 2 reads state
            value = manager2.get_state("shared_key")
            assert value == {"from": "manager1"}
            
            # Manager 2 updates state
            manager2.set_state("shared_key", {"from": "manager2"})
            
            # Manager 1 reads updated state
            value = manager1.get_state("shared_key")
            assert value == {"from": "manager2"}
            
        finally:
            manager1.close()
            manager2.close()
    
    def test_lock_prevents_concurrent_writes(self, state_config):
        """Test that locks prevent concurrent writes from multiple instances"""
        if not REDIS_AVAILABLE:
            pytest.skip("Redis not available")
        
        manager1 = DistributedStateManager(state_config)
        manager2 = DistributedStateManager(state_config)
        
        if not manager1.use_redis or not manager2.use_redis:
            pytest.skip("Redis connection failed")
        
        try:
            # Manager 1 acquires lock
            lock1 = manager1.get_lock("exclusive_resource")
            acquired1 = lock1.acquire(blocking=False)
            assert acquired1
            
            # Manager 2 tries to acquire same lock (should fail)
            lock2 = manager2.get_lock("exclusive_resource")
            acquired2 = lock2.acquire(blocking=False)
            assert not acquired2
            
            # Manager 1 releases lock
            lock1.release()
            
            # Now manager 2 can acquire
            acquired2 = lock2.acquire(blocking=False)
            assert acquired2
            lock2.release()
            
        finally:
            manager1.close()
            manager2.close()


# Integration test that requires manual verification
def test_manual_multi_instance():
    """
    Manual test to verify multi-instance coordination.
    
    Run this test in multiple terminals simultaneously:
    
    Terminal 1: pytest tests/test_distributed_state.py::test_manual_multi_instance
    Terminal 2: pytest tests/test_distributed_state.py::test_manual_multi_instance
    
    Both should complete successfully without conflicts.
    """
    if not REDIS_AVAILABLE:
        pytest.skip("Redis not available")
    
    config = DistributedStateConfig(
        redis_url="redis://localhost:6379",
        redis_db=3,
        key_prefix="manual_test",
    )
    
    manager = DistributedStateManager(config)
    
    if not manager.use_redis:
        pytest.skip("Redis connection failed")
    
    try:
        # Increment shared counter with lock
        for i in range(5):
            with manager.lock("shared_counter"):
                current = manager.get_state("counter", default=0)
                time.sleep(0.1)  # Simulate work
                manager.set_state("counter", current + 1)
                print(f"Instance {manager.instance_id[:8]}: incremented counter to {current + 1}")
        
        # Wait a bit for other instances
        time.sleep(2)
        
        # Check final count
        final_count = manager.get_state("counter", default=0)
        print(f"Final counter value: {final_count}")
        
    finally:
        manager.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
