from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from redis.exceptions import ConnectionError, TimeoutError

from collections import defaultdict

import sys
import json
import asyncio
from harmony.app.core import settings
from typing import Set

from .websocket import WebSocketManager

import structlog
logger = structlog.get_logger(__name__)

class RedisPubSubManager:
    """
    Layer 1: Manages Redis Subscriptions.
    """
    def __init__(self, ws_manager: WebSocketManager):
        self.redis_url = settings.REDIS_URL
        self.ws_manager = ws_manager
        self.listening_task = None
        self._subscribed_channels: Set[str] = set()
        self.stall_timeout = settings.REDIS_STALL_TIMEOUT
        
        # Lock per channel to avoid race conditions 99% of the time, allowing concurrent subscriptions to different channels.
        self._subscription_lock = defaultdict(asyncio.Lock)  
        
    async def connect(self):
        """
        Initializes the connection and starts the listener loop.
        """
        try:
            # Parse Redis options from settings, excluding retry parameters since we're using a custom retry strategy
            redis_kwargs = settings.redis_opts.model_dump(
                exclude={"retry_retries", "retry_cap", "retry_base"}
            )

            redis_kwargs["retry"] = Retry(
                ExponentialBackoff(
                    cap=settings.redis_opts.retry_cap, 
                    base=settings.redis_opts.retry_base
                ), 
                retries=settings.redis_opts.retry_retries
            )

            # Connect to Redis
            self.redis = Redis.from_url(
                self.redis_url, 
                decode_responses=True,
                retry_on_timeout=True,
                retry_on_error=[ConnectionError, TimeoutError],
                **redis_kwargs
            )
            self.pubsub = self.redis.pubsub()
            
            # Dummy subscription to avoid crashing redis on listen without any channels
            # Also establishes connection (redis is lazy and won't connect until the first command is issued)
            await self.pubsub.subscribe("system:dummy_keepalive")  
            logger.info("redis_connection_established")
        except Exception as e:
            logger.exception("redis_connection_failed")
            sys.exit(1)
        
    def start_listen(self):
        # Start the infinite listener loop
        self.listening_task = asyncio.create_task(self._listener_loop())
        logger.info("redis_listener_started")

    async def disconnect(self):
        if self.listening_task:
            self.listening_task.cancel()
            try:
                await self.listening_task
            except asyncio.CancelledError:
                pass
        await self.redis.close()
        logger.info("redis_disconnected")

    async def subscribe_to_chat(self, chat_id: str):
        """
        Idempotent subscription: Only subscribe to Redis if we aren't already listening.
        """
        async with self._subscription_lock[chat_id]:
            if chat_id in self._subscribed_channels: return

            logger.info("redis_channel_subscribed", chat_id=chat_id)
            await self.pubsub.subscribe(chat_id)
            self._subscribed_channels.add(chat_id)

    async def unsubscribe_from_chat(self, chat_id: str):
        """
        Cleanup: Unsubscribe if no local clients are left for this chat.
        """
        async with self._subscription_lock[chat_id]:
            if not (chat_id in self._subscribed_channels) or self.ws_manager.is_chat_active_locally(chat_id): return
            
            logger.info("redis_channel_unsubscribed", chat_id=chat_id)
            await self.pubsub.unsubscribe(chat_id)
            self._subscribed_channels.remove(chat_id)

    async def publish(self, chat_id: str, message: dict):
        try:
            await self.redis.publish(chat_id, json.dumps(message))
        except (ConnectionError, TimeoutError) as e:
            logger.exception("redis_publish_failed", chat_id=chat_id)
            raise e

    async def _listener_loop(self):
        """
        Infinite loop that reads from Redis PubSub and passes data to WS Manager.
        """
        try:
            while True:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=self.stall_timeout)
                if not message: continue
                # logger.debug("Redis message received", chat_id=message["channel"], payload_size=len(message["data"]))
                if message["type"] == "message":
                    chat_id = message["channel"]
                    payload = message["data"]
                    # Pass the message to Layer 2 for local fan-out
                    await self.ws_manager.broadcast_local(chat_id, payload)
        except asyncio.CancelledError:
            logger.info("redis_listener_cancelled")
        except Exception as e:
            logger.exception("redis_listener_critical_error")
            sys.exit(1)  # Ensure the process exits if the listener loop ends unexpectedly