import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import structlog

from harmony.app.core.interfaces import TaskQueue
from harmony.app.repositories import ChatDataRepository, UserChatRepository
from harmony.app.core import settings
from harmony.app.schemas import ChatMetaData, ChatCreateRequest, ChatResponse
from ..command import Command
from .event import ChatEventHandler

logger = structlog.get_logger(__name__)

class ChatCommands(Command):
    MAX_USERS = settings.CHAT_MAX_USERS_PER_OPERATION

    def __init__(
        self, 
        session: AsyncSession,
        chat_data_repository: ChatDataRepository,
        user_chat_repository: UserChatRepository,
        chat_event_handler: Optional[ChatEventHandler] = None,
        task_queue: Optional[TaskQueue] = None
    ):
        super().__init__(session, logger)
        self.chat_data_repo = chat_data_repository
        self.user_chat_repo = user_chat_repository
        self.chat_event_handler = chat_event_handler
        self.task_queue = task_queue

    async def _require_membership(self, user_id: uuid.UUID, chat_id: uuid.UUID):
        is_member = await self.user_chat_repo.check_user_in_chat(chat_id=chat_id, user_id=user_id, lock=True)
        if not is_member:
            logger.warning("action_denied_not_a_member", chat_id=chat_id, user_id=user_id)
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You must be a member of the chat to perform this action.")

    async def create_chat(self, creator_id: uuid.UUID, data: ChatCreateRequest) -> ChatResponse:
        # 1. Validate
        user_id_list = list(set(data.user_id_list + [creator_id]))
        if len(user_id_list) > self.MAX_USERS:
            logger.warning("create_chat_exceeds_max_users", creator_id=creator_id, requested_count=len(user_id_list))
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Limit of {self.MAX_USERS} users exceeded.")
        
        # 2. Parse metadata
        metadata = ChatMetaData(
            title=data.title, 
            description=data.description
        )

        # 3. Create
        async with self.transaction_handler("create_chat", creator_id=creator_id, target_users=len(user_id_list)):
            chat = await self.chat_data_repo.create_chat(metadata=metadata) 
            await self.session.flush() # Ensure chat.chat_id is populated
            await self.user_chat_repo.add_users_to_chat(chat_id=chat.chat_id, user_id_list=user_id_list)
            
        logger.info("chat_created", chat_id=chat.chat_id, creator_id=creator_id)
        return chat
        
    async def add_users_to_chat(self, chat_id: uuid.UUID, user_id: uuid.UUID, user_id_list: list[uuid.UUID]):
        # 1. Validate
        user_id_list = list(set(user_id_list))
        if not user_id_list:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "user_id_list cannot be empty")
        if user_id in user_id_list:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "user_id_list cannot contain the requesting user_id")
        if len(user_id_list) > self.MAX_USERS:
            logger.warning("add_users_to_chat_exceeds_max_users", chat_id=chat_id, requested_count=len(user_id_list))
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Limit of {self.MAX_USERS} users exceeded.")
        
        # 2. Authorize and Create
        async with self.transaction_handler("add_users", chat_id=chat_id, user_id=user_id):
            await self._require_membership(user_id=user_id, chat_id=chat_id)
            await self.user_chat_repo.add_users_to_chat(chat_id=chat_id, user_id_list=user_id_list)
        logger.info("users_added_to_chat", chat_id=chat_id, added_user_count=len(user_id_list))

        if self.chat_event_handler:
            self.task_queue.add_task(
                self.chat_event_handler.on_users_added_to_chat,
                chat_id=chat_id, user_id_list=user_id_list
            )

    async def leave_chat(self, user_id: uuid.UUID, chat_id: uuid.UUID):
        # 1. Attempt to Delete Membership (also serves as a membership check)
        async with self.transaction_handler("leave_chat", chat_id=chat_id, user_id=user_id):
            await self.user_chat_repo.remove_user_from_chat(chat_id=chat_id, user_id=user_id)
        logger.info("chat_left", chat_id=chat_id, user_id=user_id)

        if self.chat_event_handler:
            self.task_queue.add_task(
                self.chat_event_handler.on_user_left_chat,
                chat_id=chat_id, user_id=user_id
            )

    async def delete_chat(self, user_id: uuid.UUID, chat_id: uuid.UUID):
        # 1. Authorize and Delete
        async with self.transaction_handler("delete_chat", chat_id=chat_id, user_id=user_id):
            await self._require_membership(user_id=user_id, chat_id=chat_id)
            await self.chat_data_repo.delete_chat(chat_id)
        logger.info("chat_deleted", chat_id=chat_id, deleted_by_user_id=user_id)

        if self.chat_event_handler:
            self.task_queue.add_task(
                self.chat_event_handler.on_chat_deleted,
                chat_id=chat_id
            )