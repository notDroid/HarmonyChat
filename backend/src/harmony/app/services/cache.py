import json
import logging
from harmony.app.core import settings
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

class CacheService:
    '''
    A simple wrapper around Redis to handle caching of JSON-serializable data with TTL support.
    Since the implementation is simple we bypass the repository pattern and interact with Redis directly from the service layer.
    '''
    CACHE_DEFAULT_TTL_SECONDS = settings.CACHE_DEFAULT_TTL_SECONDS
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        
    async def get_json(self, key: str) -> dict | None:
        try:
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        except RedisError as e:
            # Catches ConnectionError, TimeoutError, etc., making this a "best effort" read
            logger.warning(f"Cache network error on GET for key", key=key, error=str(e))
            return None
        except json.JSONDecodeError as e:
            logger.exception(f"Cache decode error for key", key=key)
            return None

    async def set_json(self, key: str, value: dict, ttl: int | None = None):
        await self.redis.set(key, json.dumps(value), ex=ttl or self.CACHE_DEFAULT_TTL_SECONDS)
        
    async def delete(self, key: str):
        await self.redis.delete(key)
        
    async def delete_pattern(self, pattern: str):
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)