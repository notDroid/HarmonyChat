# import asyncio
# import logging
# import json
# from typing import Dict, Set
# from fastapi import WebSocket
# from redis.asyncio import Redis

# class WebSocketManager:
#     """
#     Manages local WebSocket connections.
#     Layer 2 Fan-out: Receives a message for a chat_id and broadcasts it to all local sockets.
#     """
#     def __init__(self):
#         # Maps chat_id -> Set of WebSocket connections
#         self.active_connections: Dict[str, Set[WebSocket]] = {}

#     async def connect(self, chat_id: str, websocket: WebSocket):
#         await websocket.accept()
#         if chat_id not in self.active_connections:
#             self.active_connections[chat_id] = set()
#         self.active_connections[chat_id].add(websocket)
#         logger.info(f"WS Connected to {chat_id}. Total local observers: {len(self.active_connections[chat_id])}")

#     def disconnect(self, chat_id: str, websocket: WebSocket):
#         if chat_id in self.active_connections:
#             self.active_connections[chat_id].remove(websocket)
#             if not self.active_connections[chat_id]:
#                 del self.active_connections[chat_id]

#     async def broadcast_local(self, chat_id: str, message: str):
#         """
#         Fan-out to local websockets.
#         """
#         if chat_id not in self.active_connections:
#             return

#         # Copy set to avoid modification during iteration
#         for connection in list(self.active_connections[chat_id]):
#             try:
#                 await connection.send_text(message)
#             except Exception as e:
#                 logger.error(f"Error sending to WS: {e}")
#                 # cleanup dead connection
#                 self.disconnect(chat_id, connection)

#     def is_chat_active_locally(self, chat_id: str) -> bool:
#         return chat_id in self.active_connections


# class RedisPubSubManager:
#     """
#     Manages Redis Subscriptions.
#     Layer 1 Fan-out: Listens to Redis channels and passes messages to WebSocketManager.
#     """
#     def __init__(self, redis_url: str, ws_manager: WebSocketManager):
#         self.redis = Redis.from_url(redis_url, decode_responses=True)
#         self.pubsub = self.redis.pubsub()
#         self.ws_manager = ws_manager
#         self.listening_task = None
#         self._subscribed_channels: Set[str] = set()

#     async def connect(self):
#         # We start the listener loop immediately.
#         # It will sit idle until we subscribe to something.
#         self.listening_task = asyncio.create_task(self._listener_loop())

#     async def disconnect(self):
#         if self.listening_task:
#             self.listening_task.cancel()
#             try:
#                 await self.listening_task
#             except asyncio.CancelledError:
#                 pass
#         await self.redis.close()

#     async def subscribe_to_chat(self, chat_id: str):
#         """
#         Only subscribe to Redis if we aren't already listening to this chat.
#         """
#         if chat_id not in self._subscribed_channels:
#             logger.info(f"Subscribing Redis to channel: {chat_id}")
#             await self.pubsub.subscribe(chat_id)
#             self._subscribed_channels.add(chat_id)

#     async def unsubscribe_from_chat(self, chat_id: str):
#         """
#         Unsubscribe if no local clients are left for this chat.
#         """
#         if chat_id in self._subscribed_channels and not self.ws_manager.is_chat_active_locally(chat_id):
#             logger.info(f"Unsubscribing Redis from channel: {chat_id}")
#             await self.pubsub.unsubscribe(chat_id)
#             self._subscribed_channels.remove(chat_id)

#     async def publish(self, chat_id: str, message: dict):
#         # Publish to the specific chat_id channel
#         await self.redis.publish(chat_id, json.dumps(message))

#     async def _listener_loop(self):
#         """
#         Infinite loop that reads from Redis PubSub and hands off to WS Manager.
#         """
#         try:
#             async for message in self.pubsub.listen():
#                 if message["type"] == "message":
#                     chat_id = message["channel"]
#                     payload = message["data"]
#                     # Handoff to Layer 2
#                     await self.ws_manager.broadcast_local(chat_id, payload)
#         except asyncio.CancelledError:
#             logger.info("Redis listener task cancelled.")
#         except Exception as e:
#             logger.error(f"Redis listener error: {e}")
#             # Optional: Add retry logic here to restart the loop