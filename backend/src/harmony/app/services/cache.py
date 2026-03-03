import json
import structlog
from harmony.app.core import CacheConfig
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = structlog.get_logger(__name__)

class CacheService:
    '''
    A simple wrapper around Redis to handle caching of JSON-serializable data with TTL support.
    The service provides "best effort" caching on reads. 
    It returns success/failure booleans for writes and deletes, allowing callers to handle failures.
    '''
    
    def __init__(self, redis_client: Redis, cache_config: CacheConfig = CacheConfig()):
        self.redis = redis_client
        self.cfg = cache_config
        
    async def get_json(self, key: str) -> dict | None:
        try:
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        except RedisError as e:
            logger.warning("cache_network_error_on_get", key=key, error=str(e))
            return None
        except json.JSONDecodeError as e:
            logger.exception("cache_decode_error", key=key)
            return None

    async def set_json(self, key: str, value: dict, ttl: int | None = None) -> bool:
        try:
            await self.redis.set(key, json.dumps(value), ex=ttl or self.cfg.default_ttl_seconds)
            return True
        except RedisError as e:
            logger.warning("cache_network_error_on_set", key=key, error=str(e))
            return False
        except Exception as e:
            logger.exception("unexpected_error_on_cache_set", key=key)
            return False
        
    async def delete(self, key: str) -> bool:
        try:
            await self.redis.delete(key)
            return True
        except RedisError as e:
            logger.warning("cache_network_error_on_delete", key=key, error=str(e))
            return False
        
    async def delete_pattern(self, pattern: str, batch_size: int = 100) -> bool:
        """
        Safely deletes keys matching a pattern using SCAN to avoid blocking Redis.
        Deletes in chunks to prevent massive memory usage and command payload limits.
        """
        try:
            keys_to_delete = []
            
            # scan_iter yields keys matching the pattern without blocking the main Redis thread
            async for key in self.redis.scan_iter(match=pattern, count=batch_size):
                keys_to_delete.append(key)
                
                # Delete in batches to avoid overwhelming the network/memory
                if len(keys_to_delete) >= batch_size:
                    await self.redis.delete(*keys_to_delete)
                    keys_to_delete.clear()
                    
            # Catch any remaining keys in the final partial batch
            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)
                
            return True
        except RedisError as e:
            logger.warning("cache_network_error_on_delete_pattern", pattern=pattern, error=str(e))
            return False
        
    async def get_many_json(self, keys: list[str]) -> list[dict | None]:
        """
        Fetches multiple keys in a single round-trip using MGET.
        Returns a list of dictionaries (or None for misses/errors) in the same order as the keys.
        """
        if not keys:
            return []
            
        try:
            raw_data = await self.redis.mget(keys)
            
            results = []
            for data in raw_data:
                try:
                    results.append(json.loads(data) if data else None)
                except json.JSONDecodeError:
                    results.append(None)
            return results
            
        except RedisError as e:
            logger.warning("cache_network_error_on_mget", keys_count=len(keys), error=str(e))
            return [None] * len(keys)
        
    async def set_many_json(self, mapping: dict[str, dict], ttl: int | None = None) -> bool:
        """
        Sets multiple keys with TTLs in a single round-trip using a pipeline.
        """
        if not mapping:
            return True
            
        try:
            async with self.redis.pipeline(transaction=False) as pipe:
                for key, value in mapping.items():
                    pipe.set(key, json.dumps(value), ex=ttl or self.cfg.default_ttl_seconds)
                await pipe.execute()
            return True
            
        except RedisError as e:
            logger.warning("cache_network_error_on_pipeline_set", keys_count=len(mapping), error=str(e))
            return False