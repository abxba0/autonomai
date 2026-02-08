"""
Cache initialization for the MainModel.

Handles setup of CacheManager and LLMResponseCache based on SystemConfig settings.
"""

import logging

from ..models.config import SystemConfig

# Cache imports
try:
    from ..cache import CacheManager, CacheConfig, CacheStrategy, LLMResponseCache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    CacheManager = None
    CacheConfig = None
    CacheStrategy = None
    LLMResponseCache = None

logger = logging.getLogger(__name__)


def initialize_cache(config: SystemConfig):
    """Initialize cache manager and LLM response cache.

    Args:
        config: System configuration with cache settings.

    Returns:
        Tuple of (cache_manager, llm_cache). Both may be None if caching
        is unavailable or initialization fails.
    """
    if not CACHE_AVAILABLE:
        logger.warning("Cache module not available. Caching disabled.")
        return None, None

    try:
        # Create cache config from system config
        cache_config = CacheConfig(
            enabled=config.enable_caching,
            redis_url=config.cache_redis_url,
            redis_db=config.cache_redis_db,
            redis_password=config.cache_redis_password,
            default_ttl=config.cache_default_ttl,
            max_memory_mb=config.cache_max_memory_mb,
            strategy=CacheStrategy(config.cache_strategy),
        )

        # Initialize cache manager
        cache_manager = CacheManager(cache_config)

        # Initialize LLM response cache
        llm_cache = LLMResponseCache(
            cache_manager=cache_manager,
            include_context_in_key=config.cache_include_context_in_key,
        )

        logger.info("Cache initialized successfully")
        return cache_manager, llm_cache

    except Exception as e:
        logger.error(f"Failed to initialize cache: {e}")
        logger.warning("Proceeding without caching")
        return None, None
