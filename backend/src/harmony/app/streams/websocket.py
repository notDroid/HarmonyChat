from typing import Dict, Set
from fastapi import WebSocket

import structlog
logger = structlog.get_logger(__name__)

class WebSocketManager:
    """
    Layer 2: Manages local WebSocket connections.
    """
    def __init__(self):
        # Maps chat_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, chat_id: str, websocket: WebSocket):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = set()
        self.active_connections[chat_id].add(websocket)
        logger.info("ws_connection_accepted", chat_id=chat_id, local_observers=len(self.active_connections[chat_id]))

    def disconnect(self, chat_id: str, websocket: WebSocket):
        if chat_id in self.active_connections:
            self.active_connections[chat_id].remove(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

    async def broadcast_local(self, chat_id: str, message: str):
        """
        Fan-out to local websockets.
        """
        if chat_id not in self.active_connections:
            return

        # Copy set to avoid modification issues during iteration if a socket disconnects mid-loop
        connections = list(self.active_connections[chat_id])
        for connection in connections:
            try:
                # Fan out to all local WS connections for this chat_id
                await connection.send_text(message)
            except Exception as e:
                logger.exception("ws_broadcast_failed", chat_id=chat_id)
                # The socket is dead, clean it up
                self.disconnect(chat_id, connection)

    def is_chat_active_locally(self, chat_id: str) -> bool:
        return chat_id in self.active_connections