import asyncio
from contextlib import AsyncExitStack
import structlog

from harmony.app.core import get_settings, setup_logging
from harmony.app.init import cache_connector, dynamodb_connector
from harmony.app.repositories import ChatHistoryRepository
from harmony.app.services import ChatEventHandler, UserEventHandler, MessageEventHandler
from harmony.app.services.cache import CacheService
from .consumer import CDCConsumer

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

        # 4. Start Consumer
        consumer = CDCConsumer(
            kafka_bootstrap_servers=settings.kafka.bootstrap_servers,
            chat_handler=chat_handler,
            user_handler=user_handler,
            message_handler=msg_handler
        )
        
        logger.info("starting_cdc_worker")
        await consumer.start()

if __name__ == "__main__":
    asyncio.run(main())