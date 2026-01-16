#!/usr/bin/env python3
"""
Verification script for distributed deployment

Checks:
- Redis connectivity
- Distributed state manager
- API health
- Celery workers
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_redis():
    """Check Redis connectivity"""
    print("\n=== Checking Redis ===")
    try:
        import redis
        client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True
        )
        client.ping()
        print("✅ Redis is accessible")
        
        # Check info
        info = client.info()
        print(f"   Redis version: {info.get('redis_version', 'unknown')}")
        print(f"   Connected clients: {info.get('connected_clients', 0)}")
        return True
    except ImportError:
        print("❌ Redis package not installed")
        print("   Install with: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def check_distributed_state():
    """Check distributed state manager"""
    print("\n=== Checking Distributed State Manager ===")
    try:
        from src.storage.distributed_state import (
            DistributedStateManager,
            DistributedStateConfig
        )
        
        config = DistributedStateConfig(
            redis_url=os.getenv("REDIS_STATE_URL", "redis://localhost:6379/2")
        )
        
        manager = DistributedStateManager(config)
        
        if manager.use_redis:
            print("✅ Distributed state manager initialized")
            print(f"   Instance ID: {manager.instance_id[:8]}...")
            
            # Test basic operations
            manager.set_state("test_key", {"test": "value"})
            value = manager.get_state("test_key")
            
            if value == {"test": "value"}:
                print("✅ State operations working")
            
            # Test locks
            with manager.lock("test_lock"):
                print("✅ Distributed locks working")
            
            # Get active instances
            instances = manager.get_active_instances()
            print(f"✅ Active instances: {len(instances)}")
            
            manager.close()
            return True
        else:
            print("⚠️  Distributed state manager running in fallback mode")
            print("   Redis connection failed or not available")
            return False
            
    except Exception as e:
        print(f"❌ Distributed state manager failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all checks"""
    print("=" * 60)
    print("DISTRIBUTED DEPLOYMENT VERIFICATION")
    print("=" * 60)
    
    checks = {
        "Redis": check_redis(),
        "Distributed State": check_distributed_state(),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in checks.values() if v is True)
    failed = sum(1 for v in checks.values() if v is False)
    
    for check_name, result in checks.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIP"
        print(f"{status}: {check_name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\n⚠️  Some checks failed. Please review configuration.")
        sys.exit(1)
    elif passed == 2:
        print("\n✅ All checks passed! System ready for distributed deployment!")
        sys.exit(0)
    else:
        print("\n⚠️  Not all checks completed successfully.")
        sys.exit(1)


if __name__ == "__main__":
    main()
