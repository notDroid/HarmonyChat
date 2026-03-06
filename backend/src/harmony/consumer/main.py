import asyncio
from contextlib import AsyncExitStack
import signal
import structlog

from harmony.app.core import get_settings, setup_logging
from harmony.app.init import cache_connector, dynamodb_connector
from harmony.app.repositories import ChatHistoryRepository
from harmony.app.services import ChatEventHandler, UserEventHandler, MessageEventHandler
from harmony.app.services.cache import CacheService

from .consumer import CDCConsumer
from .handlers import setup_router

logger = structlog.get_logger(__name__)

async def main():
    settings = get_settings()
    setup_logging(is_local_dev=(settings.app_env == "development"))
    
    async with AsyncExitStack() as stack:
        # 1. Init Cache
        redis_client = await stack.enter_async_context(cache_connector(settings.redis))
        cache_service = CacheService(redis_client, settings.cache)
        
        # 2. Init DynamoDB
        dynamo_client = await stack.enter_async_context(dynamodb_connector(settings.dynamodb, settings.aws))
        chat_history_repo = ChatHistoryRepository(dynamo_client, settings.dynamodb)

        # 3. Init Handlers
        chat_handler = ChatEventHandler(cache_service)
        user_handler = UserEventHandler(cache_service)
        msg_handler = MessageEventHandler(chat_history_repo)

        router = setup_router(chat_handler, user_handler, msg_handler)

        # 4. Start Consumer
        consumer = CDCConsumer(
            kafka_bootstrap_servers=settings.kafka.bootstrap_servers,
            topics=settings.kafka.topics,
            router=router
        )
        
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
            
        logger.info("starting_cdc_worker")
        
        # Run consumer until stop_event is set
        consumer_task = asyncio.create_task(consumer.start(stop_event))
        await stop_event.wait()
        
        logger.info("shutting_down_cdc_worker")
        await consumer_task

if __name__ == "__main__":
    asyncio.run(main())