import redis.asyncio as redis
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Redis connection pool
redis_client: Optional[redis.Redis] = None

async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    redis_client = await redis.from_url(
        f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}",
        decode_responses=True,
        encoding="utf-8"
    )
    await redis_client.ping()
    logger.info("✅ Redis connected successfully")
    return redis_client

async def close_redis():
    """Close Redis connection"""
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")

async def get_redis():
    """Get Redis client (initializes if needed)"""
    global redis_client
    if redis_client is None:
        await init_redis()
    return redis_client