import uuid
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from harmony.app.repositories import UserDataRepository, UserChatRepository
from harmony.app.models import User
from harmony.app.schemas import UserChatItem
from pydantic import EmailStr, TypeAdapter

email_adapter = TypeAdapter(EmailStr)

logger = structlog.get_logger(__name__)

class UserQueries:
    """
    Handles all read-only operations (Queries) for the User domain.
    Does not mutate state.
    """
    def __init__(
        self, 
        session: AsyncSession,
        user_data_repository: UserDataRepository,
        user_chat_repository: UserChatRepository,
    ):
        self.session = session
        self.user_data_repo = user_data_repository
        self.user_chat_repo = user_chat_repository

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.user_data_repo.get_user_by_id(user_id)
        if not user:
            logger.warning("get_user_not_found", user_id=str(user_id))
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist.")
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        # Validate email
        try:
            email_adapter.validate_python(email)
        except ValueError:
            logger.warning("get_user_by_email_invalid_format", email=email)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid email format.")
        
        user = await self.user_data_repo.get_user_by_email(email)
        if not user:
            logger.warning("get_user_by_email_not_found", email=email)
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist.")
        return user
    
    async def search_users_by_email(self, email_query: str, limit: int = 10) -> list[User]:
        if not email_query or len(email_query) < 2:
            return []
        return await self.user_data_repo.search_users_by_email(email_query, limit=limit)

    async def check_user_exists(self, user_id: uuid.UUID) -> bool:
        """
        Checks if a user exists and is actively participating.
        Returns False if the user does not exist or if they are tombstoned.
        """
        user = await self.user_data_repo.get_user_by_id(user_id)
        if user and getattr(user, "tombstone", False):
            return False
        return user is not None

    async def get_user_chats(self, user_id: uuid.UUID) -> List[UserChatItem]:
        try:
            rows = await self.user_chat_repo.get_user_chats(user_id=user_id)
            return [UserChatItem(chat_id=row.chat_id, meta=row.meta) for row in rows]
        except Exception as e:
            logger.exception("get_user_chats_failed", user_id=str(user_id))
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, 
                "An unexpected error occurred while fetching user chats."
            )
        
    async def get_users_dict(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, User]:
        return await self.user_data_repo.get_users_by_ids(user_ids)