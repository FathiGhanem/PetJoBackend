"""Token blacklist management using Redis."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from redis import Redis
from redis.exceptions import RedisError

from core.config import settings

logger = logging.getLogger(__name__)

# Redis client for token blacklist
redis_client: Optional[Redis] = None


def init_redis():
    """Initialize Redis connection for token blacklist."""
    global redis_client
    try:
        redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        # Test connection
        redis_client.ping()
        logger.info("Redis connected successfully for token blacklist")
    except RedisError as e:
        logger.warning(f"Redis connection failed: {e}. Token blacklist will be disabled.")
        redis_client = None


async def blacklist_token(token: str, expires_in_seconds: int):
    """
    Add a token to the blacklist.
    
    Args:
        token: The JWT token to blacklist
        expires_in_seconds: How long to keep the token in blacklist (should match token expiry)
    """
    if redis_client is None:
        logger.warning("Redis not available, cannot blacklist token")
        return
    
    try:
        # Store token with expiration
        redis_client.setex(
            f"blacklist:{token}",
            expires_in_seconds,
            "1"
        )
        logger.info(f"Token blacklisted successfully (expires in {expires_in_seconds}s)")
    except RedisError as e:
        logger.error(f"Failed to blacklist token: {e}")


async def is_token_blacklisted(token: str) -> bool:
    """
    Check if a token is blacklisted.
    
    Args:
        token: The JWT token to check
        
    Returns:
        True if token is blacklisted, False otherwise
    """
    if redis_client is None:
        # If Redis is not available, don't block users
        return False
    
    try:
        result = redis_client.exists(f"blacklist:{token}")
        return bool(result)
    except RedisError as e:
        logger.error(f"Failed to check token blacklist: {e}")
        # On error, don't block users
        return False


async def blacklist_refresh_token(user_id: str, token: str):
    """
    Blacklist a refresh token on logout.
    
    Args:
        user_id: The user ID
        token: The refresh token to blacklist
    """
    # Refresh tokens last 7 days
    expires_in = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    await blacklist_token(token, expires_in)
    
    # Also store by user_id for invalidating all user's refresh tokens
    if redis_client is not None:
        try:
            redis_client.sadd(f"user_tokens:{user_id}", token)
            redis_client.expire(f"user_tokens:{user_id}", expires_in)
        except RedisError as e:
            logger.error(f"Failed to track user token: {e}")


async def invalidate_all_user_tokens(user_id: str):
    """
    Invalidate all tokens for a user (e.g., on password change).
    
    Args:
        user_id: The user ID
    """
    if redis_client is None:
        return
    
    try:
        # Get all tokens for this user
        tokens = redis_client.smembers(f"user_tokens:{user_id}")
        
        # Blacklist each token
        for token in tokens:
            await blacklist_token(token, settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
        
        # Clear the user's token set
        redis_client.delete(f"user_tokens:{user_id}")
        
        logger.info(f"Invalidated {len(tokens)} tokens for user {user_id}")
    except RedisError as e:
        logger.error(f"Failed to invalidate user tokens: {e}")


def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client is not None:
        try:
            redis_client.close()
            logger.info("Redis connection closed")
        except RedisError as e:
            logger.error(f"Error closing Redis connection: {e}")
        redis_client = None
