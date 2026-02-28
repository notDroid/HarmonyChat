import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from harmony.app.repositories import ChatDataRepository, UserChatRepository
from harmony.app.schemas import ChatSchema
from ..cache import CacheService

logger = structlog.get_logger(__name__)

class ChatQueries:
    """
    Handles all read-only operations (Queries) for the Chat domain.
    Does not mutate state.
    """

    # TODO: inherit from settings
    CACHE_MEMBERSHIP_TTL_SECONDS = 300
    CACHE_CHAT_METADATA_TTL_SECONDS = 300

    @staticmethod
    def _membership_key(chat_id: uuid.UUID, user_id: uuid.UUID) -> str:
        return f"chat:{chat_id}:members:{user_id}"

    @staticmethod
    def _metadata_key(chat_id: uuid.UUID) -> str:
        return f"chat:{chat_id}:metadata"

    def __init__(
        self, 
        session: AsyncSession,
        chat_data_repository: ChatDataRepository,
        user_chat_repository: UserChatRepository,
        cache_service: CacheService | None = None,
    ):
        self.session = session
        self.chat_data_repo = chat_data_repository
        self.user_chat_repo = user_chat_repository
        self.cache_service = cache_service

    async def check_user_in_chat(self, user_id: uuid.UUID, chat_id: uuid.UUID) -> bool:
        # 1. Check cache first (if available)
        if self.cache_service:
            cache_key = self._membership_key(chat_id, user_id)
            is_member = await self.cache_service.get_json(cache_key)
            if is_member is not None:
                logger.debug("membership_cache_hit", chat_id=str(chat_id), user_id=str(user_id), is_member=is_member)
                return is_member
            
            logger.debug("membership_cache_miss", chat_id=str(chat_id), user_id=str(user_id))

        # 2. Fallback to database check
        is_member = await self.user_chat_repo.check_user_in_chat(chat_id=chat_id, user_id=user_id)
        
        # 3. Populate cache for future checks (if available)
        if self.cache_service:
            try:
                cache_key = self._membership_key(chat_id, user_id)
                await self.cache_service.set_json(cache_key, is_member, expire=self.CACHE_MEMBERSHIP_TTL_SECONDS)
                logger.debug("membership_cache_set", chat_id=str(chat_id), user_id=str(user_id), is_member=is_member)
            except Exception as e:
                logger.exception("membership_cache_set_failed", chat_id=str(chat_id), user_id=str(user_id))

        return is_member
    
    async def _require_membership(self, user_id: uuid.UUID, chat_id: uuid.UUID) -> None:
        is_member = await self.check_user_in_chat(user_id, chat_id)

        if not is_member:
            logger.warning("chat_metadata_access_denied", chat_id=str(chat_id), user_id=str(user_id))
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You must be a member of the chat to view its metadata.")

    async def get_chat_metadata(self, user_id: uuid.UUID, chat_id: uuid.UUID) -> ChatSchema:
        # 1. Authorize
        await self._require_membership(user_id, chat_id)

        # 2. Fetch from cache (if available)
        if self.cache_service:
            cache_key = self._metadata_key(chat_id)
            cached_metadata = await self.cache_service.get_json(cache_key)
            if cached_metadata is not None:
                logger.debug("chat_metadata_cache_hit", chat_id=str(chat_id), user_id=str(user_id))
                return ChatSchema(**cached_metadata)

        # 3. Fetch from database if cache miss or cache unavailable
        chat = await self.chat_data_repo.get_chat(chat_id)
        if not chat:
            logger.warning("get_chat_not_found", chat_id=str(chat_id), user_id=str(user_id))
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat does not exist.")
        chat = ChatSchema.model_validate(chat) # Convert from SQLAlchemy model to Pydantic schema
        
        # 4. Populate cache for future requests (if available)
        if self.cache_service:
            try:
                cache_key = self._metadata_key(chat_id)
                await self.cache_service.set_json(cache_key, chat.model_dump(mode="json"), expire=self.CACHE_CHAT_METADATA_TTL_SECONDS)
                logger.debug("chat_metadata_cache_set", chat_id=str(chat_id), user_id=str(user_id))
            except Exception as e:
                logger.exception("chat_metadata_cache_set_failed", chat_id=str(chat_id), user_id=str(user_id))
        
        return chat

    async def get_chat_members(self, user_id: uuid.UUID, chat_id: uuid.UUID) -> list[uuid.UUID]:
        # 1. Authorize
        await self._require_membership(user_id, chat_id)
        
        # 2. Fetch from database (membership list is not cached due to potential size and volatility, but could be optimized in the future if needed)
        users = await self.user_chat_repo.get_chat_users(chat_id=chat_id)
        if not users:
            logger.warning("get_chat_members_not_found", chat_id=str(chat_id), user_id=str(user_id))
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat does not exist.")
            
        return users