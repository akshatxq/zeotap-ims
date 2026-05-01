import redis.asyncio as redis
import os
import logging
import json
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Global variables
redis_client: Optional[redis.Redis] = None

async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = os.getenv('REDIS_PORT', '6379')
        
        redis_client = await redis.from_url(
            f"redis://{redis_host}:{redis_port}",
            decode_responses=True,
            encoding="utf-8"
        )
        await redis_client.ping()
        logger.info("✅ Redis connected successfully")
        return redis_client
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise

async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")

async def get_redis():
    """Get Redis client (initializes if needed)"""
    global redis_client
    if redis_client is None:
        await init_redis()
    return redis_client

async def cache_get(key: str) -> Optional[Any]:
    """Get cached value from Redis"""
    redis = await get_redis()
    value = await redis.get(key)
    if value:
        try:
            return json.loads(value)
        except:
            return value
    return None

async def cache_set(key: str, value: Any, ttl: int = 10) -> None:
    """Set cached value in Redis with TTL"""
    redis = await get_redis()
    serialized = json.dumps(value, default=str)
    await redis.setex(key, ttl, serialized)

async def cache_invalidate(key: str) -> None:
    """Invalidate a cache key"""
    redis = await get_redis()
    await redis.delete(key)

async def cache_dashboard_incidents(incidents: list, ttl: int = 10) -> None:
    """Cache active incidents for dashboard"""
    await cache_set("dashboard:active_incidents", incidents, ttl)

async def get_cached_dashboard_incidents() -> Optional[list]:
    """Get cached active incidents"""
    return await cache_get("dashboard:active_incidents")

async def invalidate_dashboard_cache() -> None:
    """Invalidate dashboard cache (call on incident updates)"""
    await cache_invalidate("dashboard:active_incidents")