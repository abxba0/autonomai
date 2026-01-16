"""
Embeddings caching wrapper for vector operations.

This module provides caching for:
- Embedding vectors
- Semantic similarity searches
- Vector database operations
"""

import hashlib
from typing import List, Optional, Tuple, Any
import logging

from .manager import CacheManager

logger = logging.getLogger(__name__)


class EmbeddingsCacheWrapper:
    """
    Cache wrapper for embeddings operations.

    Caches:
    - Generated embeddings for text
    - Frequently accessed embeddings from vector DB
    """

    def __init__(
        self,
        cache_manager: CacheManager,
        namespace: str = "embeddings",
    ):
        """
        Initialize embeddings cache wrapper

        Args:
            cache_manager: Underlying cache manager
            namespace: Namespace for embedding cache keys
        """
        self.cache_manager = cache_manager
        self.namespace = namespace

        # Metrics
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info("EmbeddingsCacheWrapper initialized")

    def _generate_embedding_key(self, text: str, model_name: str = "default") -> str:
        """
        Generate cache key for embedding

        Args:
            text: Text to embed
            model_name: Name of embedding model

        Returns:
            Cache key (SHA256 hash)
        """
        # Normalize text
        normalized_text = text.strip().lower()

        # Generate key
        key_string = f"{model_name}:{normalized_text}"
        cache_key = hashlib.sha256(key_string.encode("utf-8")).hexdigest()

        return cache_key

    def get_cached_embedding(
        self, text: str, model_name: str = "default"
    ) -> Optional[List[float]]:
        """
        Get cached embedding vector for text

        Args:
            text: Text to get embedding for
            model_name: Name of embedding model

        Returns:
            Embedding vector or None if not cached
        """
        try:
            cache_key = self._generate_embedding_key(text, model_name)
            cached_value = self.cache_manager.get(cache_key, namespace=self.namespace)

            if cached_value is not None:
                self.cache_hits += 1
                logger.debug(f"Embedding cache HIT for key: {cache_key[:16]}...")
                return cached_value
            else:
                self.cache_misses += 1
                logger.debug(f"Embedding cache MISS for key: {cache_key[:16]}...")
                return None

        except Exception as e:
            logger.error(f"Error getting cached embedding: {e}")
            return None

    def cache_embedding(
        self,
        text: str,
        embedding: List[float],
        model_name: str = "default",
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache embedding vector

        Args:
            text: Text that was embedded
            embedding: Embedding vector
            model_name: Name of embedding model
            ttl: Time-to-live in seconds (None uses default)

        Returns:
            True if cached successfully
        """
        try:
            cache_key = self._generate_embedding_key(text, model_name)

            success = self.cache_manager.set(
                cache_key, embedding, ttl=ttl, namespace=self.namespace
            )

            if success:
                logger.debug(f"Cached embedding for key: {cache_key[:16]}...")
            else:
                logger.warning(f"Failed to cache embedding for key: {cache_key[:16]}...")

            return success

        except Exception as e:
            logger.error(f"Error caching embedding: {e}")
            return False

    def get_or_compute_embedding(
        self,
        text: str,
        compute_fn: callable,
        model_name: str = "default",
        ttl: Optional[int] = None,
    ) -> Optional[List[float]]:
        """
        Get embedding from cache or compute and cache it

        Args:
            text: Text to embed
            compute_fn: Function to compute embedding if not cached
            model_name: Name of embedding model
            ttl: Time-to-live in seconds

        Returns:
            Embedding vector or None if computation fails
        """
        # Try to get from cache first
        cached_embedding = self.get_cached_embedding(text, model_name)
        if cached_embedding is not None:
            return cached_embedding

        # Compute embedding
        try:
            embedding = compute_fn(text)
            if embedding is not None:
                # Cache for future use
                self.cache_embedding(text, embedding, model_name, ttl)
            return embedding
        except Exception as e:
            logger.error(f"Error computing embedding: {e}")
            return None

    def invalidate_embedding(self, text: str, model_name: str = "default") -> bool:
        """
        Invalidate cached embedding for specific text

        Args:
            text: Text to invalidate
            model_name: Name of embedding model

        Returns:
            True if successful
        """
        try:
            cache_key = self._generate_embedding_key(text, model_name)
            return self.cache_manager.delete(cache_key, namespace=self.namespace)
        except Exception as e:
            logger.error(f"Error invalidating embedding: {e}")
            return False

    def get_metrics(self) -> dict:
        """
        Get cache performance metrics

        Returns:
            Dictionary with cache metrics
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total_requests,
            "hit_rate_percent": hit_rate,
        }

    def reset_metrics(self):
        """Reset cache metrics"""
        self.cache_hits = 0
        self.cache_misses = 0

    def clear(self) -> bool:
        """
        Clear all cached embeddings

        Returns:
            True if successful
        """
        try:
            return self.cache_manager.clear(namespace=self.namespace)
        except Exception as e:
            logger.error(f"Error clearing embeddings cache: {e}")
            return False

    def warm_cache(
        self, texts: List[str], compute_fn: callable, model_name: str = "default"
    ) -> int:
        """
        Pre-warm cache with frequently used embeddings

        Args:
            texts: List of texts to pre-compute embeddings for
            compute_fn: Function to compute embeddings
            model_name: Name of embedding model

        Returns:
            Number of embeddings successfully cached
        """
        cached_count = 0

        for text in texts:
            try:
                # Check if already cached
                if self.get_cached_embedding(text, model_name) is not None:
                    cached_count += 1
                    continue

                # Compute and cache
                embedding = compute_fn(text)
                if embedding is not None:
                    if self.cache_embedding(text, embedding, model_name):
                        cached_count += 1

            except Exception as e:
                logger.error(f"Error warming cache for text: {e}")

        logger.info(f"Warmed cache with {cached_count}/{len(texts)} embeddings")
        return cached_count
