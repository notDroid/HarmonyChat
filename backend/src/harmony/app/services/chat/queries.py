import uuid
import asyncio
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

    async def get_chat_metadata(self, chat_id: uuid.UUID) -> dict:
        chat = await self.chat_data_repo.get_chat(chat_id)
        if not chat:
            logger.warning("get_chat_not_found", chat_id=str(chat_id))
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat does not exist.")
        
        return chat.metadata

    async def get_chat_members(self, chat_id: uuid.UUID) -> list[uuid.UUID]:
        users = await self.user_chat_repo.get_chat_users(chat_id=chat_id)
        if not users:
            logger.warning("get_chat_members_not_found", chat_id=str(chat_id))
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat does not exist.")
        return users

    async def get_user_chats(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        chats = await self.user_chat_repo.get_user_chats(user_id=user_id)
        return chats

    async def check_user_in_chat(self, user_id: uuid.UUID, chat_id: uuid.UUID) -> bool:
        return await self.user_chat_repo.check_user_in_chat(chat_id=chat_id, user_id=user_id)