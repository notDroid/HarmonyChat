from typing import Optional
import uuid

from fastapi import logger
import structlog
from ..cache import CacheService

logger = structlog.get_logger(__name__)

class ChatEventHandler:
    @staticmethod
    def _membership_key(chat_id: uuid.UUID, user_id: uuid.UUID) -> str:
        return f"chat:{chat_id}:members:{user_id}"

    @staticmethod
    def _metadata_key(chat_id: uuid.UUID) -> str:
        return f"chat:{chat_id}:metadata"
    
    def __init__(
        self,
        cache_service: Optional[CacheService] = None
    ):
        self.cache_service = cache_service

    async def on_users_added_to_chat(self, chat_id: uuid.UUID, user_id_list: list[uuid.UUID]):
        # Clear the "not a member" cache for the newly added users
        if self.cache_service:
            for new_user_id in user_id_list:
                await self.cache_service.delete(self._membership_key(chat_id, new_user_id))
            logger.debug("membership_cache_cleared_for_added_users", chat_id=chat_id, user_ids=[str(uid) for uid in user_id_list])

    async def on_user_left_chat(self, chat_id: uuid.UUID, user_id: uuid.UUID):
        # Invalidate membership cache
        if self.cache_service:
            await self.cache_service.delete(self._membership_key(chat_id, user_id))
            logger.debug("membership_cache_cleared_for_user", chat_id=chat_id, user_id=user_id)

    async def on_chat_deleted(self, chat_id: uuid.UUID):
        # Invalidate metadata and membership caches
        if self.cache_service:
            # Delete metadata cache and ALL membership caches for this chat
            await self.cache_service.delete(self._metadata_key(chat_id))
            await self.cache_service.delete_pattern(self._membership_key(chat_id, "*"))
