"""
Example demonstrating the caching layer for performance improvements.

This example shows:
1. Basic LLM response caching
2. Embeddings caching
3. Performance measurements
4. Cache metrics
"""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from models.config import SystemConfig
from core.main_model import MainModel
from core.instruction_manager import InstructionManager
from core.validator import ValidationPipeline


def measure_time(func):
    """Decorator to measure execution time"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed
    return wrapper


def example_llm_cache():
    """Demonstrate LLM response caching"""
    print("\n" + "=" * 60)
    print("Example 1: LLM Response Caching")
    print("=" * 60)

    # Configure with caching enabled
    config = SystemConfig(
        main_model="gpt-3.5-turbo",
        enable_caching=True,
        cache_llm_responses=True,
        cache_default_ttl=3600,  # 1 hour
        enable_auto_validation=False,  # Disable for demo simplicity
    )

    # Initialize components
    instruction_manager = InstructionManager(config)
    validation_pipeline = ValidationPipeline()
    model = MainModel(config, instruction_manager, validation_pipeline)

    # Test queries
    queries = [
        "What is 2+2?",
        "Explain Python in one sentence.",
        "What is 2+2?",  # Repeated - should hit cache
    ]

    print("\nExecuting queries...\n")

    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query}")
        
        start = time.time()
        result = model.execute(query)
        elapsed = time.time() - start
        
        cache_hit = result.get("cache_hit", False)
        print(f"  Response: {result['output'][:80]}...")
        print(f"  Cache hit: {cache_hit}")
        print(f"  Time: {elapsed*1000:.2f}ms")
        
        if cache_hit:
            print("  ✓ Instant response from cache!")
        print()

    # Show cache metrics
    if model.llm_cache:
        metrics = model.llm_cache.get_metrics()
        print("\nCache Metrics:")
        print(f"  Total requests: {metrics['total_requests']}")
        print(f"  Cache hits: {metrics['cache_hits']}")
        print(f"  Cache misses: {metrics['cache_misses']}")
        print(f"  Hit rate: {metrics['hit_rate_percent']:.1f}%")


def example_embeddings_cache():
    """Demonstrate embeddings caching"""
    print("\n" + "=" * 60)
    print("Example 2: Embeddings Caching")
    print("=" * 60)

    try:
        from utils.embeddings import EmbeddingsManager
    except ImportError:
        print("\nEmbeddings module not available (requires sentence-transformers)")
        print("Install with: pip install -e \".[local]\"")
        return

    # Configure with embeddings caching
    config = SystemConfig(
        enable_caching=True,
        cache_embeddings=True,
        cache_default_ttl=7200,  # 2 hours
    )

    # Initialize embeddings manager
    embeddings = EmbeddingsManager(config)

    if not embeddings.embeddings_model:
        print("\nEmbeddings model not initialized")
        print("This is expected if sentence-transformers is not installed")
        return

    # Test texts
    texts = [
        "The system encountered a validation error",
        "Database connection timeout",
        "The system encountered a validation error",  # Repeated
    ]

    print("\nGenerating embeddings...\n")

    for i, text in enumerate(texts, 1):
        print(f"Text {i}: {text}")
        
        start = time.time()
        embedding = embeddings.get_embedding(text)
        elapsed = time.time() - start
        
        if embedding:
            print(f"  Embedding size: {len(embedding)}")
            print(f"  Time: {elapsed*1000:.2f}ms")
            
            if elapsed < 0.01:  # Less than 10ms likely means cache hit
                print("  ✓ Retrieved from cache!")
        else:
            print("  Failed to generate embedding")
        print()

    # Show cache metrics
    if embeddings.cache_wrapper:
        metrics = embeddings.cache_wrapper.get_metrics()
        print("\nEmbeddings Cache Metrics:")
        print(f"  Total requests: {metrics['total_requests']}")
        print(f"  Cache hits: {metrics['cache_hits']}")
        print(f"  Cache misses: {metrics['cache_misses']}")
        print(f"  Hit rate: {metrics['hit_rate_percent']:.1f}%")


def example_cache_warming():
    """Demonstrate cache warming"""
    print("\n" + "=" * 60)
    print("Example 3: Cache Warming")
    print("=" * 60)

    from cache import CacheManager, CacheConfig, EmbeddingsCacheWrapper

    # Initialize cache
    config = CacheConfig(
        enabled=True,
        redis_url="redis://localhost:6379",  # Will fallback to memory if unavailable
    )
    cache_manager = CacheManager(config)
    embeddings_cache = EmbeddingsCacheWrapper(cache_manager)

    # Mock embedding function for demo
    def mock_embedding(text):
        """Simulate embedding computation"""
        time.sleep(0.01)  # Simulate 10ms computation
        return [0.1] * 384  # Return fake embedding

    # Frequently used failure patterns
    common_failures = [
        "validation error",
        "network timeout",
        "authentication failed",
        "database connection error",
        "insufficient permissions",
        "rate limit exceeded",
        "invalid request format",
        "service unavailable",
    ]

    print(f"\nWarming cache with {len(common_failures)} common patterns...")
    
    start = time.time()
    cached_count = embeddings_cache.warm_cache(
        common_failures,
        mock_embedding
    )
    elapsed = time.time() - start

    print(f"✓ Warmed cache with {cached_count}/{len(common_failures)} embeddings")
    print(f"  Time: {elapsed*1000:.2f}ms")
    
    # Now accessing these will be instant
    print("\nAccessing warmed embeddings...")
    for pattern in common_failures[:3]:
        start = time.time()
        embedding = embeddings_cache.get_cached_embedding(pattern)
        elapsed = time.time() - start
        
        if embedding:
            print(f"  ✓ {pattern}: {elapsed*1000:.3f}ms (cached)")


def example_performance_comparison():
    """Compare performance with and without caching"""
    print("\n" + "=" * 60)
    print("Example 4: Performance Comparison")
    print("=" * 60)

    from cache import CacheManager, CacheConfig, LLMResponseCache

    # Initialize cache
    config = CacheConfig(enabled=True)
    cache_manager = CacheManager(config)
    llm_cache = LLMResponseCache(cache_manager)

    # Simulate expensive LLM call
    def expensive_llm_call(query):
        time.sleep(0.1)  # Simulate 100ms LLM call
        return {
            "output": f"Response to: {query}",
            "validation_passed": True,
        }

    query = "What is the meaning of life?"
    system_instructions = "You are a helpful assistant."
    model_name = "test-model"
    temperature = 0.7

    # Measure without cache (first call)
    print("\n1. First call (cache miss):")
    start = time.time()
    response = expensive_llm_call(query)
    llm_cache.cache_response(
        query, system_instructions, model_name, temperature, response
    )
    no_cache_time = time.time() - start
    print(f"   Time: {no_cache_time*1000:.2f}ms")

    # Measure with cache (second call)
    print("\n2. Second call (cache hit):")
    start = time.time()
    cached_response = llm_cache.get_cached_response(
        query, system_instructions, model_name, temperature
    )
    cache_time = time.time() - start
    print(f"   Time: {cache_time*1000:.2f}ms")

    # Calculate speedup
    speedup = no_cache_time / cache_time
    print(f"\n✓ Speedup: {speedup:.1f}x faster with cache!")
    print(f"  Savings: {(no_cache_time - cache_time)*1000:.2f}ms per cached query")


def example_cache_strategies():
    """Demonstrate different cache strategies"""
    print("\n" + "=" * 60)
    print("Example 5: Cache Strategies")
    print("=" * 60)

    from cache import CacheManager, CacheConfig, CacheStrategy

    strategies = [
        CacheStrategy.TTL,
        CacheStrategy.LRU,
        CacheStrategy.LFU,
        CacheStrategy.MANUAL,
    ]

    for strategy in strategies:
        print(f"\nStrategy: {strategy}")
        
        config = CacheConfig(
            enabled=True,
            strategy=strategy,
            default_ttl=60,
        )
        cache = CacheManager(config)

        # Store some data
        cache.set("key1", "value1", namespace="test")
        cache.set("key2", "value2", namespace="test")

        # Get stats
        stats = cache.get_stats()
        print(f"  Backend: {stats['backend']}")
        print(f"  Strategy: {stats['strategy']}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Caching Layer Examples")
    print("=" * 60)
    print("\nDemonstrating production caching features:")
    print("- LLM response caching")
    print("- Embeddings caching")
    print("- Cache warming")
    print("- Performance measurements")
    print("- Cache strategies")

    try:
        example_llm_cache()
    except Exception as e:
        print(f"\nExample 1 error: {e}")

    try:
        example_embeddings_cache()
    except Exception as e:
        print(f"\nExample 2 error: {e}")

    try:
        example_cache_warming()
    except Exception as e:
        print(f"\nExample 3 error: {e}")

    try:
        example_performance_comparison()
    except Exception as e:
        print(f"\nExample 4 error: {e}")

    try:
        example_cache_strategies()
    except Exception as e:
        print(f"\nExample 5 error: {e}")

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
