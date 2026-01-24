"""Caching utilities (using in-memory cache for now)."""

from typing import Optional, Any, Callable
from functools import wraps
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Simple in-memory cache
_cache = {}
_cache_ttl = {}


def clear_cache():
    """Clear all cache entries."""
    global _cache, _cache_ttl
    _cache.clear()
    _cache_ttl.clear()
    logger.info("Cache cleared")


def get_from_cache(key: str) -> Optional[Any]:
    """Get value from cache if not expired."""
    if key not in _cache:
        return None
    
    # Check if expired
    if key in _cache_ttl and datetime.now() > _cache_ttl[key]:
        del _cache[key]
        del _cache_ttl[key]
        return None
    
    logger.debug(f"Cache hit: {key}")
    return _cache[key]


def set_to_cache(key: str, value: Any, ttl_seconds: int = 300):
    """Set value to cache with TTL."""
    _cache[key] = value
    _cache_ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)
    logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)


def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """Decorator to cache function results."""
    
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Check cache
            cached_value = get_from_cache(key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            set_to_cache(key, result, ttl_seconds)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Check cache
            cached_value = get_from_cache(key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Store in cache
            set_to_cache(key, result, ttl_seconds)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# For production, consider using Redis:
# from redis import asyncio as aioredis
# from fastapi_cache import FastAPICache
# from fastapi_cache.backends.redis import RedisBackend
# 
# async def init_cache():
#     redis = aioredis.from_url("redis://localhost")
#     FastAPICache.init(RedisBackend(redis), prefix="petjo:")
