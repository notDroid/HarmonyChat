import asyncio
import logging
import json
from typing import Dict, Set
from fastapi import WebSocket
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

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
        logger.info(f"WS Connected to {chat_id}. Local observers: {len(self.active_connections[chat_id])}")

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
                logger.error(f"Error sending to WS: {e}")
                # The socket is dead, clean it up
                self.disconnect(chat_id, connection)

    def is_chat_active_locally(self, chat_id: str) -> bool:
        return chat_id in self.active_connections


class RedisPubSubManager:
    """
    Layer 1: Manages Redis Subscriptions.
    """
    def __init__(self, redis_url: str, ws_manager: WebSocketManager):
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        self.ws_manager = ws_manager
        self.listening_task = None
        self._subscribed_channels: Set[str] = set()

    async def connect(self):
        """
        Initializes the connection and starts the listener loop.
        """
        try:
            # 1. Health Check
            await self.redis.ping()
            logger.info("Redis: Connection established.")
            
            # 2. Create PubSub instance inside the async context
            self.pubsub = self.redis.pubsub()
            
            # 3. Start the infinite listener loop
            self.listening_task = asyncio.create_task(self._listener_loop())
            logger.info("Redis: Listener task started.")
            
        except Exception as e:
            logger.error(f"Redis: Failed to connect: {e}")
            raise e

    async def disconnect(self):
        if self.listening_task:
            self.listening_task.cancel()
            try:
                await self.listening_task
            except asyncio.CancelledError:
                pass
        await self.redis.close()
        logger.info("Redis: Disconnected.")

    async def subscribe_to_chat(self, chat_id: str):
        """
        Idempotent subscription: Only subscribe to Redis if we aren't already listening.
        """
        if chat_id not in self._subscribed_channels:
            logger.info(f"Redis: Subscribing to channel {chat_id}")
            await self.pubsub.subscribe(chat_id)
            self._subscribed_channels.add(chat_id)

    async def unsubscribe_from_chat(self, chat_id: str):
        """
        Cleanup: Unsubscribe if no local clients are left for this chat.
        """
        if chat_id in self._subscribed_channels and not self.ws_manager.is_chat_active_locally(chat_id):
            logger.info(f"Redis: Unsubscribing from channel {chat_id}")
            await self.pubsub.unsubscribe(chat_id)
            self._subscribed_channels.remove(chat_id)

    async def publish(self, chat_id: str, message: dict):
        await self.redis.publish(chat_id, json.dumps(message))

    async def _listener_loop(self):
        """
        Infinite loop that reads from Redis PubSub and passes data to WS Manager.
        """
        try:
            async for message in self.pubsub.listen():
                logger.info(f"Redis message received on channel {message['channel']}: {message['data']}")
                if message["type"] == "message":
                    chat_id = message["channel"]
                    payload = message["data"]
                    # Pass the message to Layer 2 for local fan-out
                    await self.ws_manager.broadcast_local(chat_id, payload)
        except asyncio.CancelledError:
            logger.info("Redis listener task cancelled.")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")