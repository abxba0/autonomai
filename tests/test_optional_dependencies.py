"""
Test optional dependencies and graceful degradation
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))


def test_embeddings_without_optional_deps():
    """Test that embeddings module works without optional dependencies"""
    print("\n=== Testing Embeddings Module ===")
    
    # Import the module - should work even if chromadb/sentence-transformers are missing
    from src.utils.embeddings import EmbeddingsManager, CHROMADB_AVAILABLE, SENTENCE_TRANSFORMERS_AVAILABLE
    from src.models.config import SystemConfig, FailureEntry
    
    print(f"ChromaDB available: {CHROMADB_AVAILABLE}")
    print(f"Sentence Transformers available: {SENTENCE_TRANSFORMERS_AVAILABLE}")
    
    # Create config
    config = SystemConfig()
    
    # Initialize embeddings manager - should not crash
    try:
        embeddings_manager = EmbeddingsManager(config)
        print("✓ EmbeddingsManager initialized successfully")
        
        # Test that it falls back to simple text similarity
        if not CHROMADB_AVAILABLE or not SENTENCE_TRANSFORMERS_AVAILABLE:
            assert embeddings_manager.embeddings_model is None, "Should fallback when dependencies missing"
            print("✓ Correctly fell back to simple text similarity")
        
        # Test creating a failure entry
        failure = FailureEntry(
            trigger_type="auto_validation",
            failure_description="Test failure",
            severity="low"
        )
        
        # Try to find similar failures - should not crash
        similar = embeddings_manager.find_similar_failures(failure)
        print(f"✓ find_similar_failures works (returned {len(similar)} results)")
        
    except Exception as e:
        print(f"✗ Failed to initialize EmbeddingsManager: {e}")
        raise
    
    print("✓ Embeddings module tests passed")


def test_rate_limit_without_redis():
    """Test that rate limiting works without redis"""
    print("\n=== Testing Rate Limit Module ===")
    
    # Import directly from rate_limit module to avoid importing fastapi dependencies from __init__
    import importlib.util
    
    # Load the rate_limit module directly
    rate_limit_path = os.path.join(os.path.dirname(__file__), "src", "security", "rate_limit.py")
    spec = importlib.util.spec_from_file_location("rate_limit", rate_limit_path)
    rate_limit_module = importlib.util.module_from_spec(spec)
    sys.modules['rate_limit'] = rate_limit_module
    spec.loader.exec_module(rate_limit_module)
    
    RateLimiter = rate_limit_module.RateLimiter
    RateLimitConfig = rate_limit_module.RateLimitConfig
    REDIS_AVAILABLE = rate_limit_module.REDIS_AVAILABLE
    FASTAPI_AVAILABLE = rate_limit_module.FASTAPI_AVAILABLE
    
    print(f"Redis available: {REDIS_AVAILABLE}")
    print(f"FastAPI available: {FASTAPI_AVAILABLE}")
    
    # Create rate limiter without redis
    config = RateLimitConfig(requests_per_minute=10)
    
    try:
        # Test with use_redis=False
        rate_limiter = RateLimiter(config, use_redis=False)
        print("✓ RateLimiter initialized with use_redis=False")
        
        # Test rate limiting
        allowed, headers = rate_limiter.check_rate_limit("test_client")
        assert allowed, "First request should be allowed"
        print("✓ Rate limiting works in memory mode")
        
        # Test with use_redis=True when redis is not available
        if not REDIS_AVAILABLE:
            rate_limiter = RateLimiter(config, use_redis=True)
            # Should fallback to in-memory
            assert not rate_limiter.use_redis, "Should fallback when Redis not available"
            print("✓ Correctly fell back to in-memory when Redis requested but not available")
        
    except Exception as e:
        print(f"✗ Failed to initialize RateLimiter: {e}")
        raise
    
    print("✓ Rate limit module tests passed")


def test_core_imports():
    """Test that core modules can be imported"""
    print("\n=== Testing Core Imports ===")
    
    try:
        from src.models.config import SystemConfig, FailureEntry
        from src.models.critic_response import CriticResponse
        print("✓ Core models imported successfully")
        
        # Test creating config
        config = SystemConfig()
        assert config is not None
        print("✓ SystemConfig instantiated successfully")
        
    except Exception as e:
        print(f"✗ Failed to import core modules: {e}")
        raise
    
    print("✓ Core imports tests passed")


def main():
    """Run all tests"""
    print("="*60)
    print("Testing Optional Dependencies and Graceful Degradation")
    print("="*60)
    
    try:
        test_core_imports()
        test_embeddings_without_optional_deps()
        test_rate_limit_without_redis()
        
        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"✗ Tests failed: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
