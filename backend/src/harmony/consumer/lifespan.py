from contextlib import asynccontextmanager, AsyncExitStack
from harmony.app.core import get_consumer_settings
from harmony.app.init import cache_connector, dynamodb_connector
from harmony.app.repositories import ChatHistoryRepository
from harmony.app.services import ChatEventHandler, UserEventHandler, MessageEventHandler
from harmony.app.services.cache import CacheService
from .context import ConsumerContext

@asynccontextmanager
async def lifespan():
    settings = get_consumer_settings()
    
    async with AsyncExitStack() as stack:
        # 1. Init Connections
        redis_client = await stack.enter_async_context(cache_connector(settings.redis))
        dynamo_client = await stack.enter_async_context(dynamodb_connector(settings.dynamodb, settings.aws))
        
        # 2. Init Repositories & Services
        cache_service = CacheService(redis_client, settings.cache)
        chat_history_repo = ChatHistoryRepository(dynamo_client, settings.dynamodb)

        # 3. Create Handlers & Context
        context = ConsumerContext(
            chat_handler=ChatEventHandler(cache_service),
            user_handler=UserEventHandler(cache_service),
            msg_handler=MessageEventHandler(chat_history_repo),
            settings=settings
        )
        
        yield context