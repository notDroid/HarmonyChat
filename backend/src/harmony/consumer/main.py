import asyncio
from contextlib import AsyncExitStack
import signal
import structlog

from harmony.app.core import get_consumer_settings, setup_logging
from harmony.app.init import cache_connector, dynamodb_connector
from harmony.app.repositories import ChatHistoryRepository
from harmony.app.services import ChatEventHandler, UserEventHandler, MessageEventHandler
from harmony.app.services.cache import CacheService

from .consumer import CDCConsumer
from .handlers import main_router
from .context import ConsumerContext
from .lifespan import lifespan

logger = structlog.get_logger(__name__)

async def main():
    settings = get_consumer_settings()
    setup_logging(is_local_dev=(settings.app_env == "development"))
    
    async with lifespan() as context:
        consumer = CDCConsumer(
            config=settings.kafka_consumer,
            router=main_router,
            context=context
        )
        
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
            
        logger.info("starting_cdc_worker")
        
        consumer_task = asyncio.create_task(consumer.start(stop_event))
        await stop_event.wait()
        
        logger.info("shutting_down_cdc_worker")
        await consumer_task

if __name__ == "__main__":
    asyncio.run(main())