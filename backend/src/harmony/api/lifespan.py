from contextlib import asynccontextmanager, AsyncExitStack
from fastapi import FastAPI
from harmony.app.core import get_api_settings
import structlog

from harmony.app.init import (
    cache_connector,
    dynamodb_connector,
    kafka_connector,
    postgres_connector
)

logger = structlog.get_logger(__name__)

async def init_cache(app, stack):
    settings = get_api_settings()
    if not settings.features.cache_redis:
        app.state.redis_cache_client = None
        return

    redis_client = await stack.enter_async_context(cache_connector(settings.redis))
    app.state.redis_cache_client = redis_client

async def init_dynamodb(app, stack):
    settings = get_api_settings()

    dynamodb_client = await stack.enter_async_context(dynamodb_connector(settings.dynamodb, settings.aws))
    app.state.dynamodb = dynamodb_client

async def init_kafka(app, stack):
    settings = get_api_settings()

    producer = await stack.enter_async_context(kafka_connector(settings.kafka_producer))
    app.state.kafka_producer = producer

async def init_postgres(app, stack):
    settings = get_api_settings()

    session_factory = await stack.enter_async_context(postgres_connector(settings.app_env == "development", settings.postgres))
    app.state.session_factory = session_factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        logger.info("system_startup_initiated")

        # --------------------------- Resources Setup -------------------------- #
        
        # 1. Postgres
        await init_postgres(app, stack)

        # 2. DynamoDB
        await init_dynamodb(app, stack)

        # 3. Cache
        await init_cache(app, stack)

        # 4. Kafka
        await init_kafka(app, stack)

        logger.info("system_startup_complete")
        
        # ----------------------------- App Running ---------------------------- #
        
        yield
        
        # --------------------------- Resources Teardown ----------------------- #
        
        logger.info("system_shutdown_initiated")
        # AsyncExitStack handles the closing of all contexts in reverse order automatically