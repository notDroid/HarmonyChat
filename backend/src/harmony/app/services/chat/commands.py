import uuid
import asyncio
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from harmony.app.repositories import ChatDataRepository, UserChatRepository
from harmony.app.core import settings

logger = structlog.get_logger(__name__)

class ChatCommands:
    MAX_USERS = settings.CHAT_MAX_USERS_PER_OPERATION

    def __init__(
        self, 
        session: AsyncSession,
        chat_data_repository: ChatDataRepository,
        user_chat_repository: UserChatRepository,
    ):
        self.session = session
        self.chat_data_repo = chat_data_repository
        self.user_chat_repo = user_chat_repository

    async def create_chat(self, creator_id: uuid.UUID, target_user_ids: list[uuid.UUID]) -> uuid.UUID:
        # Add creator to the list of users to add to the chat
        # Ensure no duplicates and enforcing the max user limit.
        user_id_list = list(set(target_user_ids + [creator_id]))
        if len(user_id_list) > self.MAX_USERS:
            logger.warning("create_chat_exceeds_max_users", creator_id=creator_id, requested_count=len(user_id_list))
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Limit of {self.MAX_USERS} users exceeded.")

        # Create chat and add users to it within a transaction.
        try:
            chat = await self.chat_data_repo.create_chat() 
            await self.session.flush()  # Ensure chat_id is generated
            await self.user_chat_repo.add_users_to_chat(chat_id=chat.chat_id, user_id_list=user_id_list)
            await self.session.commit()
            
            logger.info("chat_created", chat_id=chat.chat_id, creator_id=creator_id)
            return chat.chat_id
        except Exception as e:
            await self.session.rollback()
            logger.exception("create_chat_failed", creator_id=creator_id)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create chat")
        
    async def add_users_to_chat(self, chat_id: uuid.UUID, user_id: uuid.UUID, user_id_list: list[uuid.UUID]):
        user_id_list = list(set(user_id_list))  # Remove duplicates
        if not user_id_list:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "user_id_list cannot be empty")
        if user_id in user_id_list:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "user_id_list cannot contain the requesting user_id")
        
        if len(user_id_list) > self.MAX_USERS:
            logger.warning("add_users_to_chat_exceeds_max_users", chat_id=chat_id, requested_count=len(user_id_list))
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Limit of {self.MAX_USERS} users exceeded.")

        try:
            await self.user_chat_repo.add_users_to_chat(chat_id=chat_id, user_id_list=user_id_list)
            await self.session.commit()
            logger.info("users_added_to_chat", chat_id=chat_id, added_user_count=len(user_id_list))
        except Exception as e:
            await self.session.rollback()
            logger.exception("add_users_to_chat_failed", chat_id=chat_id)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to add users to chat")

    async def leave_chat(self, user_id: uuid.UUID, chat_id: uuid.UUID):
        try:
            await self.user_chat_repo.remove_user_from_chat(chat_id=chat_id, user_id=user_id)
            await self.session.commit()
            logger.info("chat_left", chat_id=chat_id, user_id=user_id)
        except Exception:
            await self.session.rollback()
            logger.exception("chat_leave_failed", chat_id=chat_id, user_id=user_id)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to leave chat")

    async def delete_chat(self, user_id: uuid.UUID, chat_id: uuid.UUID):
        try:
            await self.chat_data_repo.delete_chat(chat_id)
            await self.session.commit()
            logger.info("chat_deleted", chat_id=chat_id, deleted_by_user_id=user_id)
        except Exception:
            await self.session.rollback()
            logger.exception("chat_delete_failed", chat_id=chat_id, user_id=user_id)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to delete chat")