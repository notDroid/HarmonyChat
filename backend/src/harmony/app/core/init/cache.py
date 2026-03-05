from contextlib import asynccontextmanager
from redis.asyncio import Redis
import structlog

from ..settings import get_settings, RedisConfig

logger = structlog.get_logger(__name__)

async def init_cache(app, stack):
    """
    Initializes the Redis Cache client and stores it in app.state.
    """
    settings = get_settings()
    if not settings.features.cache_redis:
        app.state.redis_cache_client = None
        return

    redis_client = await stack.enter_async_context(cache_connector(settings.redis))
    app.state.redis_cache_client = redis_client

@asynccontextmanager
async def cache_connector(cfg: RedisConfig):
    """
    Context manager that yields a connected Redis client configured for caching.
    Handles connection retries, backoff, and graceful teardown.
    """

    # Instantiate the client with retry behaviors
    redis_client = Redis.from_url(
        cfg.url,
        decode_responses=True,
        health_check_interval=cfg.health_check_interval,
        socket_timeout=cfg.request_timeout_ms / 1000,  # Convert ms to seconds
        retry_on_timeout=False,
    )

    try:
        # Force a connection attempt immediately so we know it's alive during startup
        await redis_client.ping()
        logger.info("redis_cache_connection_established")
        
        yield redis_client
    except Exception as e:
        logger.exception("redis_cache_connection_failed")
        raise e
    finally:
        # Gracefully close the connection pool when the lifespan tears down
        await redis_client.aclose()
        logger.info("redis_cache_disconnected")