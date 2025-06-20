from loguru import logger

import redis
from core.settings import settings

RATE_LIMIT = 10
WINDOW = 60

redis_client = None


async def initialize_redis():
    global redis_client

    logger.info(f"Start redis connection - {settings.REDIS_URI!r}")
    redis_client = redis.Redis.from_url(settings.REDIS_URI)
    redis_client.ping()
    logger.info(f"Connection with redis successfully established")


async def is_rate_limited(identifier: str) -> bool:
    key = f"rate_limit:{identifier}"
    count = redis_client.incr(key)
    logger.info(f"Rate limiter increased by 1 to total {count}")

    if count == 1:
        redis_client.expire(key, WINDOW)

    return count > RATE_LIMIT
