from contextlib import asynccontextmanager, AsyncExitStack
from fastapi import FastAPI
import structlog

from harmony.app.db.postgres import postgres_connector
from harmony.app.db.dynamodb import dynamodb_connector
from harmony.app.streams import stream_connector

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        logger.info("system_startup_initiated")

        # --------------------------- Resources Setup -------------------------- #
        
        # 1. Postgres
        app.state.session_factory = await stack.enter_async_context(postgres_connector())
        
        # 2. DynamoDB
        app.state.dynamodb = await stack.enter_async_context(dynamodb_connector())

        # 3. Redis & WebSockets
        redis, ws = await stack.enter_async_context(stream_connector())
        app.state.redis_manager = redis
        app.state.ws_manager = ws

        logger.info("system_startup_complete")
        
        # ----------------------------- App Running ---------------------------- #
        
        yield
        
        # --------------------------- Resources Teardown ----------------------- #
        
        logger.info("system_shutdown_initiated")
        # AsyncExitStack handles the closing of all contexts in reverse order automatically