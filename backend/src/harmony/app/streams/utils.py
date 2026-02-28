from contextlib import asynccontextmanager
from harmony.app.core import settings
from .pubsub import RedisPubSubManager
from .websocket import WebSocketManager

@asynccontextmanager
async def stream_connector():
    """
    Context manager that yields (RedisManager, WebSocketManager).
    Handles Redis connection and listener loop.
    """
    if not settings.PS_ENABLE_REDIS:
        yield None, None
        return

    ws_manager = WebSocketManager()
    redis_manager = RedisPubSubManager(ws_manager)

    # 1. Connect
    await redis_manager.connect()

    # 2. Start Listening (Background Task inside manager)
    if settings.PS_ENABLE_REDIS_LISTEN:
        redis_manager.start_listen()

    try:
        yield redis_manager, ws_manager
    finally:
        # 3. Disconnect
        await redis_manager.disconnect()