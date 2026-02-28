import uuid
import structlog
from typing import Optional
from ..cache import CacheService

logger = structlog.get_logger(__name__)

class UserEventHandler:

    @staticmethod
    def _user_cache_key(user_id: uuid.UUID) -> str:
        return f"user:{user_id}"
    
    def __init__(
        self,
        cache_service: Optional[CacheService] = None
    ):
        self.cache_service = cache_service

    async def on_delete_user(self, user_id: uuid.UUID):
        if self.cache_service:
            # Invalidate any cached user data to prevent stale reads of deleted user
            cache_key = self._user_cache_key(user_id)
            await self.cache_service.delete(cache_key)