import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

# Fixed the import to bring in UserDataRepository
from harmony.app.repositories import UserDataRepository, UserChatRepository
from harmony.app.schemas import UserCreateRequest, UserMetaData
from ..command import Command

logger = structlog.get_logger(__name__)

class UserCommands(Command):
    def __init__(
        self, 
        session: AsyncSession,
        user_data_repository: UserDataRepository, # Corrected type hint
        user_chat_repository: UserChatRepository,
    ):
        super().__init__(session, logger)
        self.user_data_repo = user_data_repository
        self.user_chat_repo = user_chat_repository

    async def create_user(self, req: UserCreateRequest, hashed_password: str) -> uuid.UUID:
        async with self.transaction_handler("create_user", email=req.email):
            
            metadata = UserMetaData(
                username=req.username if req.username else req.email
            ).model_dump()
            
            user = await self.user_data_repo.create_user(
                email=req.email,
                hashed_password=hashed_password,
                metadata=metadata
            )
            
            await self.session.flush()

        logger.info("user_created", user_id=str(user.user_id), email=req.email)
        return user.user_id

    async def delete_user(self, user_id: uuid.UUID):
        async with self.transaction_handler("delete_user", user_id=user_id):
            await self.user_data_repo.make_user_tombstone(user_id=user_id)
            
        logger.info("user_tombstoned", user_id=str(user_id))