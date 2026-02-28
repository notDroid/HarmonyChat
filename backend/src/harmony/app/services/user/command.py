import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

# Fixed the import to bring in UserDataRepository
from harmony.app.repositories import UserDataRepository, UserChatRepository
from harmony.app.schemas import UserCreateRequest, UserMetaData
from ..command import Command
from .event import UserEventHandler

logger = structlog.get_logger(__name__)

class UserCommands(Command):
    def __init__(
        self, 
        session: AsyncSession,
        user_data_repository: UserDataRepository,
        user_chat_repository: UserChatRepository,
        user_event_handler: UserEventHandler | None = None
    ):
        super().__init__(session, logger)
        self.user_data_repo = user_data_repository
        self.user_chat_repo = user_chat_repository
        self.user_event_handler = user_event_handler

    async def create_user(self, req: UserCreateRequest, hashed_password: str) -> uuid.UUID:
        # 1. Handle request->metadata transformation
        metadata = UserMetaData(
            username=req.username if req.username else req.email,
        )

        # 2. Create user (and validate email uniqueness)
        async with self.transaction_handler("create_user", email=req.email):    
            user = await self.user_data_repo.create_user(
                email=req.email,
                hashed_password=hashed_password,
                metadata=metadata
            )
            
            await self.session.flush()

        logger.info("user_created", user_id=str(user.user_id), email=req.email)
        return user

    async def delete_user(self, user_id: uuid.UUID):
        async with self.transaction_handler("delete_user", user_id=user_id):
            await self.user_data_repo.make_user_tombstone(user_id=user_id)
            
        logger.info("user_tombstoned", user_id=str(user_id))

        if self.user_event_handler:
            await self.user_event_handler.on_delete_user(user_id=user_id)