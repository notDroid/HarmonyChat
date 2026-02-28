from contextlib import asynccontextmanager
from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from redis.exceptions import ConnectionError, TimeoutError
import structlog

from harmony.app.core import settings

logger = structlog.get_logger(__name__)

async def init_cache(app, stack):
    """
    Initializes the Redis Cache client and stores it in app.state.
    """
    if not settings.ENABLE_CACHE_REDIS:
        app.state.redis_cache_client = None
        return

    redis_client = await stack.enter_async_context(cache_connector())
    app.state.redis_cache_client = redis_client

@asynccontextmanager
async def cache_connector():
    """
    Context manager that yields a connected Redis client configured for caching.
    Handles connection retries, backoff, and graceful teardown.
    """
    # Configure the infinite exponential backoff strategy
    retry_strategy = Retry(
        ExponentialBackoff(
            cap=settings.CACHE_redis_opts.retry_cap,
            base=settings.CACHE_redis_opts.retry_base
        ),
        retries=settings.CACHE_redis_opts.retry_retries
    )

    # Instantiate the client with retry behaviors
    redis_client = Redis.from_url(
        settings.CACHE_REDIS_URL,
        decode_responses=True,
        health_check_interval=settings.CACHE_redis_opts.health_check_interval,
        retry_on_timeout=True,
        retry_on_error=[ConnectionError, TimeoutError],
        retry=retry_strategy
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