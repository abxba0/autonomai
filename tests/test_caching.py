"""
Tests for the caching layer - correctness, concurrency, and performance
"""

import sys
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_cache_imports():
    """Test that cache module imports work"""
    try:
        from cache import (
            CacheManager,
            CacheConfig,
            CacheStrategy,
            LLMResponseCache,
            EmbeddingsCacheWrapper,
        )

        assert CacheManager is not None
        assert CacheConfig is not None
        assert CacheStrategy is not None
        assert LLMResponseCache is not None
        assert EmbeddingsCacheWrapper is not None

        print("✓ Cache module imports work")
        return True
    except ImportError as e:
        print(f"✗ Cache imports failed: {e}")
        print("This is expected if redis is not installed")
        return False


def test_cache_manager_memory_backend():
    """Test CacheManager with in-memory backend (no Redis required)"""
    from cache import CacheManager, CacheConfig, CacheStrategy

    # Create config with caching enabled but no Redis
    config = CacheConfig(
        enabled=True,
        redis_url="redis://invalid:9999",  # Invalid URL to force memory backend
        default_ttl=60,
        strategy=CacheStrategy.TTL,
    )

    # Initialize cache manager (should fallback to memory)
    cache = CacheManager(config)

    # Test basic set/get
    assert cache.set("test_key", "test_value", namespace="test")
    assert cache.get("test_key", namespace="test") == "test_value"

    # Test non-existent key
    assert cache.get("nonexistent", namespace="test") is None

    # Test delete
    assert cache.delete("test_key", namespace="test")
    assert cache.get("test_key", namespace="test") is None

    # Test exists
    cache.set("exists_key", "value", namespace="test")
    assert cache.exists("exists_key", namespace="test") is True
    assert cache.exists("nonexistent", namespace="test") is False

    # Test clear
    cache.set("key1", "value1", namespace="test")
    cache.set("key2", "value2", namespace="test")
    assert cache.clear(namespace="test")
    assert cache.get("key1", namespace="test") is None
    assert cache.get("key2", namespace="test") is None

    print("✓ CacheManager memory backend works")


def test_cache_manager_complex_objects():
    """Test caching of complex Python objects"""
    from cache import CacheManager, CacheConfig, CacheStrategy

    config = CacheConfig(enabled=True, redis_url="redis://invalid:9999")
    cache = CacheManager(config)

    # Test dict
    test_dict = {"key": "value", "nested": {"a": 1, "b": 2}}
    cache.set("dict_key", test_dict, namespace="test")
    retrieved = cache.get("dict_key", namespace="test")
    assert retrieved == test_dict

    # Test list
    test_list = [1, 2, 3, "four", {"five": 5}]
    cache.set("list_key", test_list, namespace="test")
    retrieved = cache.get("list_key", namespace="test")
    assert retrieved == test_list

    print("✓ CacheManager handles complex objects")


def test_cache_ttl_expiration():
    """Test TTL-based cache expiration"""
    from cache import CacheManager, CacheConfig, CacheStrategy

    config = CacheConfig(
        enabled=True,
        redis_url="redis://invalid:9999",
        default_ttl=2,  # 2 seconds
        strategy=CacheStrategy.TTL,
    )
    cache = CacheManager(config)

    # Set value with short TTL
    cache.set("ttl_key", "ttl_value", ttl=1, namespace="test")
    assert cache.get("ttl_key", namespace="test") == "ttl_value"

    # Wait for expiration
    time.sleep(2)
    assert cache.get("ttl_key", namespace="test") is None

    print("✓ TTL expiration works")


def test_llm_response_cache():
    """Test LLM response caching"""
    from cache import CacheManager, CacheConfig, LLMResponseCache

    config = CacheConfig(enabled=True, redis_url="redis://invalid:9999")
    cache_manager = CacheManager(config)
    llm_cache = LLMResponseCache(cache_manager)

    # Test caching a response
    user_query = "What is 2+2?"
    system_instructions = "You are a helpful assistant."
    model_name = "test-model"
    temperature = 0.7
    response = {
        "output": "The answer is 4.",
        "validation_passed": True,
        "validation_results": [],
    }

    # Cache response
    assert llm_cache.cache_response(
        user_query, system_instructions, model_name, temperature, response
    )

    # Retrieve cached response
    cached = llm_cache.get_cached_response(
        user_query, system_instructions, model_name, temperature
    )
    assert cached is not None
    assert cached["output"] == "The answer is 4."

    # Test cache miss with different query
    cached = llm_cache.get_cached_response(
        "What is 3+3?", system_instructions, model_name, temperature
    )
    assert cached is None

    # Check metrics
    metrics = llm_cache.get_metrics()
    assert metrics["cache_hits"] == 1
    assert metrics["cache_misses"] == 1
    assert metrics["total_requests"] == 2

    print("✓ LLM response cache works")


def test_llm_cache_with_context():
    """Test LLM cache with conversation context"""
    from cache import CacheManager, CacheConfig, LLMResponseCache

    config = CacheConfig(enabled=True, redis_url="redis://invalid:9999")
    cache_manager = CacheManager(config)
    llm_cache = LLMResponseCache(
        cache_manager, include_context_in_key=True
    )

    user_query = "What did I just ask?"
    system_instructions = "You are helpful."
    model_name = "test-model"
    temperature = 0.7
    context = [
        {"role": "user", "content": "What is 2+2?"},
        {"role": "assistant", "content": "4"},
    ]
    response = {"output": "You asked what is 2+2?"}

    # Cache with context
    llm_cache.cache_response(
        user_query, system_instructions, model_name, temperature, response,
        conversation_context=context
    )

    # Should get cache hit with same context
    cached = llm_cache.get_cached_response(
        user_query, system_instructions, model_name, temperature,
        conversation_context=context
    )
    assert cached is not None

    # Should get cache miss with different context
    different_context = [{"role": "user", "content": "Hello"}]
    cached = llm_cache.get_cached_response(
        user_query, system_instructions, model_name, temperature,
        conversation_context=different_context
    )
    assert cached is None

    print("✓ LLM cache with context works")


def test_embeddings_cache():
    """Test embeddings caching"""
    from cache import CacheManager, CacheConfig, EmbeddingsCacheWrapper

    config = CacheConfig(enabled=True, redis_url="redis://invalid:9999")
    cache_manager = CacheManager(config)
    embeddings_cache = EmbeddingsCacheWrapper(cache_manager)

    # Mock embedding computation
    def mock_compute_embedding(text: str):
        # Return a fake embedding vector
        return [0.1, 0.2, 0.3, 0.4, 0.5]

    # Test get_or_compute
    text = "This is a test sentence."
    embedding = embeddings_cache.get_or_compute_embedding(
        text, mock_compute_embedding
    )
    assert embedding is not None
    assert len(embedding) == 5

    # Second call should hit cache
    embedding2 = embeddings_cache.get_or_compute_embedding(
        text, mock_compute_embedding
    )
    assert embedding2 == embedding

    # Check metrics
    metrics = embeddings_cache.get_metrics()
    assert metrics["cache_hits"] == 1
    assert metrics["cache_misses"] == 1

    print("✓ Embeddings cache works")


def test_embeddings_cache_warm():
    """Test cache warming for embeddings"""
    from cache import CacheManager, CacheConfig, EmbeddingsCacheWrapper

    config = CacheConfig(enabled=True, redis_url="redis://invalid:9999")
    cache_manager = CacheManager(config)
    embeddings_cache = EmbeddingsCacheWrapper(cache_manager)

    # Mock embedding computation
    def mock_compute_embedding(text: str):
        return [0.1] * 5

    # Warm cache with multiple texts
    texts = ["text1", "text2", "text3"]
    cached_count = embeddings_cache.warm_cache(texts, mock_compute_embedding)
    assert cached_count == 3

    # All should now be cached
    for text in texts:
        embedding = embeddings_cache.get_cached_embedding(text)
        assert embedding is not None

    print("✓ Cache warming works")


def test_cache_concurrency():
    """Test cache thread safety and concurrent access"""
    from cache import CacheManager, CacheConfig

    config = CacheConfig(enabled=True, redis_url="redis://invalid:9999")
    cache = CacheManager(config)

    results = []
    errors = []

    def worker(worker_id: int):
        """Worker function for concurrent access"""
        try:
            for i in range(10):
                key = f"concurrent_key_{i}"
                value = f"worker_{worker_id}_value_{i}"

                # Set value
                cache.set(key, value, namespace="concurrent")

                # Get value
                retrieved = cache.get(key, namespace="concurrent")

                # Verify
                if retrieved is not None:
                    results.append((worker_id, i, retrieved))
        except Exception as e:
            errors.append((worker_id, e))

    # Run multiple workers concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, i) for i in range(5)]
        for future in as_completed(futures):
            future.result()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) > 0

    print(f"✓ Cache concurrency test passed ({len(results)} operations)")


def test_cache_performance():
    """Test cache performance improvements"""
    from cache import CacheManager, CacheConfig, LLMResponseCache

    config = CacheConfig(enabled=True, redis_url="redis://invalid:9999")
    cache_manager = CacheManager(config)
    llm_cache = LLMResponseCache(cache_manager)

    # Simulate expensive LLM call
    def expensive_llm_call(query: str):
        time.sleep(0.01)  # Simulate 10ms LLM call
        return {"output": f"Response to: {query}"}

    user_query = "Test query"
    system_instructions = "Test instructions"
    model_name = "test-model"
    temperature = 0.7

    # First call - cache miss
    start = time.time()
    response = expensive_llm_call(user_query)
    llm_cache.cache_response(
        user_query, system_instructions, model_name, temperature, response
    )
    first_call_time = time.time() - start

    # Second call - cache hit
    start = time.time()
    cached = llm_cache.get_cached_response(
        user_query, system_instructions, model_name, temperature
    )
    cache_call_time = time.time() - start

    assert cached is not None
    assert cache_call_time < first_call_time

    print(f"✓ Cache performance: {first_call_time*1000:.2f}ms vs {cache_call_time*1000:.2f}ms (speedup: {first_call_time/cache_call_time:.1f}x)")


def test_cache_invalidation():
    """Test cache invalidation strategies"""
    from cache import CacheManager, CacheConfig, LLMResponseCache

    config = CacheConfig(enabled=True, redis_url="redis://invalid:9999")
    cache_manager = CacheManager(config)
    llm_cache = LLMResponseCache(cache_manager)

    # Cache some responses
    for i in range(5):
        llm_cache.cache_response(
            f"query_{i}",
            "instructions",
            "model",
            0.7,
            {"output": f"response_{i}"},
        )

    # Verify they're cached
    cached = llm_cache.get_cached_response("query_0", "instructions", "model", 0.7)
    assert cached is not None

    # Clear all cached responses
    assert llm_cache.clear()

    # Verify cache is empty
    cached = llm_cache.get_cached_response("query_0", "instructions", "model", 0.7)
    assert cached is None

    print("✓ Cache invalidation works")


def test_cache_stats():
    """Test cache statistics reporting"""
    from cache import CacheManager, CacheConfig

    config = CacheConfig(enabled=True, redis_url="redis://invalid:9999")
    cache = CacheManager(config)

    # Perform some operations
    cache.set("key1", "value1", namespace="test")
    cache.set("key2", "value2", namespace="test")
    cache.get("key1", namespace="test")
    cache.get("nonexistent", namespace="test")

    # Get stats
    stats = cache.get_stats()
    assert stats["enabled"] is True
    assert stats["backend"] == "memory"
    assert stats["strategy"] == "ttl"

    print("✓ Cache statistics work")


def test_cache_health_check():
    """Test cache health check"""
    from cache import CacheManager, CacheConfig

    config = CacheConfig(enabled=True, redis_url="redis://invalid:9999")
    cache = CacheManager(config)

    # Health check should pass for memory backend
    assert cache.health_check() is True

    print("✓ Cache health check works")


def run_all_tests():
    """Run all cache tests"""
    print("\n" + "=" * 60)
    print("Running Cache Layer Tests")
    print("=" * 60 + "\n")

    test_functions = [
        test_cache_imports,
        test_cache_manager_memory_backend,
        test_cache_manager_complex_objects,
        test_cache_ttl_expiration,
        test_llm_response_cache,
        test_llm_cache_with_context,
        test_embeddings_cache,
        test_embeddings_cache_warm,
        test_cache_concurrency,
        test_cache_performance,
        test_cache_invalidation,
        test_cache_stats,
        test_cache_health_check,
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            print(f"\nRunning: {test_func.__name__}")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
