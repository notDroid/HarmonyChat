import structlog
from fastapi import WebSocket, WebSocketDisconnect
from harmony.app.streams import WebSocketManager, RedisPubSubManager
from .chat import ChatQueries

logger = structlog.get_logger(__name__)

class StreamService:
    """
    Orchestrates the lifecycle of a real-time connection.
    Bridges domain logic (authorization) with infrastructure (WS/Redis).
    """
    def __init__(
        self, 
        ws_manager: WebSocketManager, 
        redis_manager: RedisPubSubManager,
        chat_queries: ChatQueries
    ):
        self.ws_manager = ws_manager
        self.redis_manager = redis_manager
        self.chat_queries = chat_queries

    async def handle_chat_connection(self, websocket: WebSocket, chat_id: str, user_id: str | None = None):
        # # 1. Authorize (will likely be implemented using tickets, rather than the chat service as hinted here)

        # 2. Accept Local Connection (Layer 2)
        await self.ws_manager.connect(chat_id, websocket)
        
        # 3. Subscribe to Global Pub/Sub (Layer 1)
        await self.redis_manager.subscribe_to_chat(chat_id)
        
        try:
            # 4. Keep connection alive
            while True:
                await websocket.receive_text()

        except WebSocketDisconnect:
            logger.info("client_disconnected", user_id=user_id, chat_id=chat_id)
        finally:
            # 5. Cleanup
            self.ws_manager.disconnect(chat_id, websocket)
            await self.redis_manager.unsubscribe_from_chat(chat_id)