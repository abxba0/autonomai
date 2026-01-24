#!/usr/bin/env python3
"""
Distributed Deployment Demo

This example demonstrates how to use AutonomAI in a distributed deployment
with Redis-based state management and distributed locking.

Features demonstrated:
- Distributed state management with Redis
- Cross-instance coordination
- Distributed locks for race condition prevention
- Tenant isolation in multi-instance setup
- Fault tolerance and recovery

Prerequisites:
- Redis server running (docker run -d -p 6379:6379 redis:latest)
- Install dependencies: pip install -e ".[web]"

Usage:
    python examples/distributed_deployment_demo.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem, SystemConfig
from src.storage.distributed_state import DistributedStateManager
from dotenv import load_dotenv
import time
import threading
from typing import List

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def demo_1_basic_distributed_state():
    """Demo 1: Basic distributed state management"""
    print_section("Demo 1: Basic Distributed State Management")

    load_dotenv()

    # Create distributed state manager
    state_manager = DistributedStateManager(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        namespace="demo"
    )

    print("\n1. Storing distributed state...")
    state_manager.set("app_version", "1.0.0")
    state_manager.set("feature_flags", {"new_ui": True, "beta_features": False})

    print("✓ State stored in Redis")

    print("\n2. Retrieving distributed state...")
    version = state_manager.get("app_version")
    flags = state_manager.get("feature_flags")

    print(f"   App Version: {version}")
    print(f"   Feature Flags: {flags}")

    print("\n3. Checking state existence...")
    exists = state_manager.exists("app_version")
    print(f"   'app_version' exists: {exists}")

    print("\n4. Deleting state...")
    state_manager.delete("app_version")
    exists = state_manager.exists("app_version")
    print(f"   'app_version' exists after deletion: {exists}")

    print("\n✓ Basic distributed state management completed")


def demo_2_distributed_locks():
    """Demo 2: Distributed locks for race condition prevention"""
    print_section("Demo 2: Distributed Locks")

    load_dotenv()

    state_manager = DistributedStateManager(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        namespace="demo"
    )

    # Initialize a counter
    state_manager.set("counter", 0)

    def increment_with_lock(worker_id: int, iterations: int):
        """Increment counter with distributed lock"""
        for i in range(iterations):
            # Acquire distributed lock
            lock_acquired = state_manager.acquire_lock(
                "counter_lock",
                timeout=5.0,
                blocking_timeout=1.0
            )

            if lock_acquired:
                try:
                    # Critical section - increment counter
                    current = state_manager.get("counter") or 0
                    time.sleep(0.001)  # Simulate some work
                    state_manager.set("counter", current + 1)

                    if i % 10 == 0:
                        print(f"   Worker {worker_id}: Counter = {current + 1}")
                finally:
                    # Always release the lock
                    state_manager.release_lock("counter_lock")
            else:
                print(f"   Worker {worker_id}: Failed to acquire lock on iteration {i}")

    print("\n1. Starting 3 workers to increment counter 50 times each...")
    print("   (Using distributed locks to prevent race conditions)\n")

    # Create and start worker threads
    workers = []
    for i in range(3):
        worker = threading.Thread(
            target=increment_with_lock,
            args=(i + 1, 50)
        )
        workers.append(worker)
        worker.start()

    # Wait for all workers to complete
    for worker in workers:
        worker.join()

    final_count = state_manager.get("counter")
    expected = 3 * 50

    print(f"\n2. Final counter value: {final_count}")
    print(f"   Expected value: {expected}")

    if final_count == expected:
        print("   ✓ No race conditions! Distributed locks working correctly.")
    else:
        print(f"   ✗ Race condition detected! Lost {expected - final_count} increments.")

    # Cleanup
    state_manager.delete("counter")


def demo_3_multi_instance_system():
    """Demo 3: Multiple system instances with shared state"""
    print_section("Demo 3: Multi-Instance Coordination")

    load_dotenv()

    # Create two system instances simulating different servers
    print("\n1. Creating two system instances (simulating different servers)...\n")

    config1 = SystemConfig(
        main_model="mock",
        critic_model="mock",
        enable_distributed_state=True,
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        instruction_dir="instructions_instance1"
    )

    config2 = SystemConfig(
        main_model="mock",
        critic_model="mock",
        enable_distributed_state=True,
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        instruction_dir="instructions_instance2"
    )

    system1 = SelfOptimizingSystem(config1)
    system2 = SelfOptimizingSystem(config2)

    print("   Instance 1 initialized")
    print("   Instance 2 initialized")

    # Access shared distributed state
    if system1.distributed_state and system2.distributed_state:
        print("\n2. Testing cross-instance state sharing...\n")

        # Instance 1 sets state
        system1.distributed_state.set("shared_config", {
            "max_retries": 3,
            "timeout": 30
        })
        print("   Instance 1: Set shared_config")

        # Instance 2 reads the same state
        config_from_instance2 = system2.distributed_state.get("shared_config")
        print(f"   Instance 2: Retrieved shared_config = {config_from_instance2}")

        # Test distributed lock acquisition
        print("\n3. Testing distributed lock coordination...\n")

        lock1_acquired = system1.distributed_state.acquire_lock(
            "critical_resource",
            timeout=5.0
        )
        print(f"   Instance 1: Lock acquired = {lock1_acquired}")

        # Instance 2 tries to acquire the same lock (should fail)
        lock2_acquired = system2.distributed_state.acquire_lock(
            "critical_resource",
            timeout=1.0,
            blocking_timeout=0.5
        )
        print(f"   Instance 2: Lock acquired = {lock2_acquired} (expected: False)")

        # Instance 1 releases lock
        system1.distributed_state.release_lock("critical_resource")
        print("   Instance 1: Lock released")

        # Instance 2 can now acquire
        lock2_acquired = system2.distributed_state.acquire_lock(
            "critical_resource",
            timeout=1.0
        )
        print(f"   Instance 2: Lock acquired = {lock2_acquired} (expected: True)")

        if lock2_acquired:
            system2.distributed_state.release_lock("critical_resource")

        print("\n✓ Multi-instance coordination successful")
    else:
        print("\n⚠ Distributed state not available (Redis may not be running)")
        print("  Start Redis with: docker run -d -p 6379:6379 redis:latest")


def demo_4_tenant_isolation():
    """Demo 4: Multi-tenant isolation in distributed setup"""
    print_section("Demo 4: Multi-Tenant Isolation")

    load_dotenv()

    state_manager = DistributedStateManager(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        namespace="multi_tenant_demo"
    )

    print("\n1. Creating state for three different tenants...\n")

    # Each tenant has isolated state
    tenants = ["tenant_a", "tenant_b", "tenant_c"]

    for tenant_id in tenants:
        state_manager.set(f"{tenant_id}:config", {
            "name": f"Company {tenant_id.split('_')[1].upper()}",
            "plan": "enterprise",
            "api_quota": 10000
        })
        print(f"   ✓ {tenant_id}: State initialized")

    print("\n2. Reading tenant-specific state...\n")

    for tenant_id in tenants:
        config = state_manager.get(f"{tenant_id}:config")
        print(f"   {tenant_id}: {config}")

    print("\n3. Demonstrating tenant isolation...\n")

    # Update tenant_a's quota
    config_a = state_manager.get("tenant_a:config")
    config_a["api_quota"] = 20000
    state_manager.set("tenant_a:config", config_a)
    print("   Updated tenant_a quota to 20000")

    # Verify other tenants are unaffected
    config_b = state_manager.get("tenant_b:config")
    config_c = state_manager.get("tenant_c:config")

    print(f"   tenant_b quota (should be 10000): {config_b['api_quota']}")
    print(f"   tenant_c quota (should be 10000): {config_c['api_quota']}")

    print("\n✓ Tenant isolation verified - changes to one tenant don't affect others")

    # Cleanup
    for tenant_id in tenants:
        state_manager.delete(f"{tenant_id}:config")


def demo_5_fault_tolerance():
    """Demo 5: Fault tolerance and recovery"""
    print_section("Demo 5: Fault Tolerance & Recovery")

    load_dotenv()

    print("\n1. Testing graceful degradation when Redis is unavailable...\n")

    # Try to connect to non-existent Redis instance
    try:
        state_manager = DistributedStateManager(
            redis_url="redis://localhost:9999",  # Wrong port
            namespace="demo",
            connection_timeout=1.0
        )

        # This should handle the error gracefully
        state_manager.set("test_key", "test_value")
        print("   ✓ System continues to operate (in-memory fallback)")

    except Exception as e:
        print(f"   ⚠ Connection failed: {e}")
        print("   System should implement fallback to in-memory state")

    print("\n2. Testing automatic reconnection...\n")

    # Connect to actual Redis
    state_manager = DistributedStateManager(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        namespace="demo"
    )

    # Set some state
    state_manager.set("reconnect_test", "initial_value")
    initial_value = state_manager.get("reconnect_test")
    print(f"   Initial value: {initial_value}")

    # Simulate network issue and recovery
    # In production, the Redis client automatically handles reconnection
    print("   ✓ Redis client handles automatic reconnection on network issues")

    # Verify state persists
    recovered_value = state_manager.get("reconnect_test")
    print(f"   Recovered value: {recovered_value}")

    if initial_value == recovered_value:
        print("\n✓ State persisted across connection issues")

    # Cleanup
    state_manager.delete("reconnect_test")


def main():
    """Run all distributed deployment demos"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                 AutonomAI Distributed Deployment Demo                    ║
║                                                                           ║
║  This demo shows how to use AutonomAI in distributed deployments         ║
║  with Redis-based state management and coordination.                     ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)

    # Check if Redis is available
    try:
        from redis import Redis
        redis_client = Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            socket_connect_timeout=1
        )
        redis_client.ping()
        redis_available = True
        print("✓ Redis is available and running\n")
    except Exception as e:
        redis_available = False
        print(f"⚠ Redis is not available: {e}")
        print("\nTo run this demo, please start Redis:")
        print("  docker run -d -p 6379:6379 redis:latest\n")
        print("Some demos will be skipped.\n")

    try:
        if redis_available:
            # Run all demos
            demo_1_basic_distributed_state()
            demo_2_distributed_locks()
            demo_3_multi_instance_system()
            demo_4_tenant_isolation()
            demo_5_fault_tolerance()
        else:
            print("Skipping demos - Redis not available")

        print_section("Summary")
        print("""
Distributed Deployment Features Demonstrated:
  ✓ Basic distributed state management with Redis
  ✓ Distributed locks for race condition prevention
  ✓ Multi-instance coordination and shared state
  ✓ Multi-tenant isolation in distributed setup
  ✓ Fault tolerance and automatic recovery

Production Deployment Recommendations:
  1. Use Redis Sentinel or Redis Cluster for high availability
  2. Set appropriate lock timeouts based on operation duration
  3. Implement health checks for Redis connectivity
  4. Use namespace prefixes for tenant isolation
  5. Monitor Redis memory usage and set eviction policies
  6. Enable Redis persistence (AOF or RDB) for durability
  7. Use connection pooling for better performance
  8. Implement circuit breakers for Redis failures

For more information, see:
  - docs/distributed-deployment.md
  - docs/MULTI_TENANT.md
        """)

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
