from contextlib import asynccontextmanager, AsyncExitStack
from fastapi import FastAPI
import structlog

from .init import (
    init_cache, 
    init_dynamodb, 
    init_postgres, 
    init_kafka,
)



logger = structlog.get_logger(__name__)

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