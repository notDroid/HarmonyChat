import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from harmony.app.repositories import ChatDataRepository, UserChatRepository

logger = structlog.get_logger(__name__)

class ChatQueries:
    """
    Handles all read-only operations (Queries) for the Chat domain.
    Does not mutate state.
    """
    def __init__(
        self, 
        session: AsyncSession,
        chat_data_repository: ChatDataRepository,
        user_chat_repository: UserChatRepository,
    ):
        self.session = session
        self.chat_data_repo = chat_data_repository
        self.user_chat_repo = user_chat_repository

    async def _check_membership(self, user_id: uuid.UUID, chat_id: uuid.UUID):
        is_member = await self.user_chat_repo.check_user_in_chat(chat_id=chat_id, user_id=user_id, lock=True)
        if not is_member:
            logger.warning("action_denied_not_a_member", chat_id=chat_id, user_id=user_id)
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You must be a member of the chat to perform this action.")

    async def get_chat_metadata(self, user_id: uuid.UUID, chat_id: uuid.UUID) -> dict:
        # 1. Authorize
        await self._check_membership(user_id, chat_id)
        
        # 2. Fetch
        chat = await self.chat_data_repo.get_chat(chat_id)
        if not chat:
            logger.warning("get_chat_not_found", chat_id=str(chat_id))
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat does not exist.")
        
        return chat.metadata

    async def get_chat_members(self, user_id: uuid.UUID, chat_id: uuid.UUID) -> list[uuid.UUID]:
        # 1. Authorize
        await self._check_membership(user_id, chat_id)
        
        # 2. Fetch
        users = await self.user_chat_repo.get_chat_users(chat_id=chat_id)
        if not users:
            logger.warning("get_chat_members_not_found", chat_id=str(chat_id))
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat does not exist.")
            
        return users

    async def check_user_in_chat(self, user_id: uuid.UUID, chat_id: uuid.UUID) -> bool:
        try:
            return await self.user_chat_repo.check_user_in_chat(chat_id=chat_id, user_id=user_id)
        except Exception as e:
            logger.exception("check_user_in_chat_failed", chat_id=chat_id, user_id=user_id)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, 
                "An unexpected error occurred while checking chat membership."
            )