"""
LLM response caching for inference optimization.

This module provides caching for LLM responses based on:
- System instructions
- User query
- Model configuration
- Conversation context (optional)
"""

import hashlib
import json
from typing import Dict, Any, Optional, List
import logging

from .manager import CacheManager, CacheConfig

logger = logging.getLogger(__name__)


class LLMResponseCache:
    """
    Cache manager specifically for LLM responses.

    Caches responses based on:
    - System instructions (or their hash)
    - User query
    - Model name and configuration
    - Optional conversation context
    """

    def __init__(
        self,
        cache_manager: CacheManager,
        namespace: str = "llm_responses",
        include_context_in_key: bool = False,
    ):
        """
        Initialize LLM response cache

        Args:
            cache_manager: Underlying cache manager
            namespace: Namespace for LLM cache keys
            include_context_in_key: Whether to include conversation context in cache key
        """
        self.cache_manager = cache_manager
        self.namespace = namespace
        self.include_context_in_key = include_context_in_key

        # Metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_errors = 0

        logger.info(
            f"LLMResponseCache initialized "
            f"(include_context: {include_context_in_key})"
        )

    def _generate_cache_key(
        self,
        user_query: str,
        system_instructions: str,
        model_name: str,
        temperature: float,
        conversation_context: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generate a deterministic cache key for LLM request

        Args:
            user_query: User's query
            system_instructions: System instructions
            model_name: Name of the model
            temperature: Model temperature
            conversation_context: Optional conversation history

        Returns:
            Cache key (SHA256 hash)
        """
        # Build components for cache key
        components = [
            f"query:{user_query}",
            f"model:{model_name}",
            f"temp:{temperature}",
        ]

        # Include system instructions (use hash for large instructions)
        if len(system_instructions) > 1000:
            instructions_hash = hashlib.sha256(
                system_instructions.encode("utf-8")
            ).hexdigest()
            components.append(f"instructions_hash:{instructions_hash}")
        else:
            components.append(f"instructions:{system_instructions}")

        # Optionally include conversation context
        if self.include_context_in_key and conversation_context:
            context_str = json.dumps(conversation_context, sort_keys=True)
            context_hash = hashlib.sha256(context_str.encode("utf-8")).hexdigest()
            components.append(f"context_hash:{context_hash}")

        # Generate final key
        key_string = "|".join(components)
        cache_key = hashlib.sha256(key_string.encode("utf-8")).hexdigest()

        return cache_key

    def get_cached_response(
        self,
        user_query: str,
        system_instructions: str,
        model_name: str,
        temperature: float,
        conversation_context: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached LLM response if available

        Args:
            user_query: User's query
            system_instructions: System instructions
            model_name: Name of the model
            temperature: Model temperature
            conversation_context: Optional conversation history

        Returns:
            Cached response dict or None if not found
        """
        try:
            cache_key = self._generate_cache_key(
                user_query,
                system_instructions,
                model_name,
                temperature,
                conversation_context,
            )

            cached_value = self.cache_manager.get(cache_key, namespace=self.namespace)

            if cached_value is not None:
                self.cache_hits += 1
                logger.debug(f"Cache HIT for key: {cache_key[:16]}...")
                return cached_value
            else:
                self.cache_misses += 1
                logger.debug(f"Cache MISS for key: {cache_key[:16]}...")
                return None

        except Exception as e:
            self.cache_errors += 1
            logger.error(f"Error getting cached response: {e}")
            return None

    def cache_response(
        self,
        user_query: str,
        system_instructions: str,
        model_name: str,
        temperature: float,
        response: Dict[str, Any],
        ttl: Optional[int] = None,
        conversation_context: Optional[List[Dict[str, str]]] = None,
    ) -> bool:
        """
        Cache LLM response

        Args:
            user_query: User's query
            system_instructions: System instructions
            model_name: Name of the model
            temperature: Model temperature
            response: Response to cache
            ttl: Time-to-live in seconds (None uses default)
            conversation_context: Optional conversation history

        Returns:
            True if cached successfully
        """
        try:
            cache_key = self._generate_cache_key(
                user_query,
                system_instructions,
                model_name,
                temperature,
                conversation_context,
            )

            success = self.cache_manager.set(
                cache_key, response, ttl=ttl, namespace=self.namespace
            )

            if success:
                logger.debug(f"Cached response for key: {cache_key[:16]}...")
            else:
                logger.warning(f"Failed to cache response for key: {cache_key[:16]}...")

            return success

        except Exception as e:
            self.cache_errors += 1
            logger.error(f"Error caching response: {e}")
            return False

    def invalidate_for_instructions(self, system_instructions: str) -> bool:
        """
        Invalidate all cached responses for specific system instructions

        Args:
            system_instructions: System instructions to invalidate

        Returns:
            True if successful

        Note:
            This is a simple implementation that clears the entire namespace.
            For production, you'd want more granular invalidation.
        """
        try:
            # For simplicity, clear entire namespace
            # In production, you'd track keys by instruction version
            logger.info("Invalidating LLM response cache")
            return self.cache_manager.clear(namespace=self.namespace)
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
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
            "cache_errors": self.cache_errors,
            "total_requests": total_requests,
            "hit_rate_percent": hit_rate,
        }

    def reset_metrics(self):
        """Reset cache metrics"""
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_errors = 0

    def clear(self) -> bool:
        """
        Clear all cached LLM responses

        Returns:
            True if successful
        """
        try:
            return self.cache_manager.clear(namespace=self.namespace)
        except Exception as e:
            logger.error(f"Error clearing LLM cache: {e}")
            return False
