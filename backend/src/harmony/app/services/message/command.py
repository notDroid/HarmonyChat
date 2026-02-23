import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from harmony.app.repositories import ChatDataRepository, UserChatRepository
from harmony.app.core import settings
from ..command import Command

logger = structlog.get_logger(__name__)

class ChatCommands(Command):
    def __init__(
        self, 
        session: AsyncSession,
        chat_data_repository: ChatDataRepository,
        user_chat_repository: UserChatRepository,
    ):
        super().__init__(session, logger)
        self.chat_data_repo = chat_data_repository
        self.user_chat_repo = user_chat_repository