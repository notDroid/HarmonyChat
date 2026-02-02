from ulid import ULID
from datetime import datetime, timezone
from fastapi import HTTPException

from simple_discord.app.schemas import *
from simple_discord.app.repositories import ChatHistoryRepository, UserChatRepository, ChatDataRepository
from simple_discord.app.db import UnitOfWorkFactory


class ChatService:
    '''
    Docstring for ChatService (Not fully implemented yet)

    This service handles chat operations including creating chats, sending messages, and retrieving chat history.
    It interacts with the ChatHistoryRepository, UserChatRepository, and ChatDataRepository to perform these operations.

    CreateChat:
        1. Validates that at least two users are provided.
        2. Validate users exist.
        3. Validate first user is friend with all other users.
        4. Generates a unique chat ID using ULID.
        5. Writes to the ChatData table and UserChat table within a transaction.

    SendMessage:
        1. Verifies that the user is a member of the chat.
        2. Generates a unique ULID for the message.
        3. Creates a ChatMessage item and stores it in the ChatHistory table.


    GetChatHistory:
        1. Verify user is member of chat.
        2. Retrieves all messages for the specified chat ID from the ChatHistory table.
    '''

    def __init__(
            self, 
            chat_history_repository: ChatHistoryRepository, 
            user_chat_repository: UserChatRepository, 
            chat_data_repository: ChatDataRepository,
            unit_of_work: UnitOfWorkFactory
        ):
        self.chat_history_repository = chat_history_repository
        self.user_chat_repository = user_chat_repository
        self.chat_data_repository = chat_data_repository
        self.uow_factory = unit_of_work

    async def create_chat(self, user_id_list: list[str]) -> str:
        if len(user_id_list) < 2:
            raise HTTPException(400, "A chat must have at least two users.")
        
        chat_id = str(ULID())
        
        chat_data_item = ChatDataItem(
            chat_id=chat_id,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        async with self.uow_factory() as uow:
            await self.chat_data_repository.create_chat(chat_data_item, uow)
            await self.user_chat_repository.create_chat(chat_id=chat_id, user_id_list=user_id_list, unit_of_work=uow)
            await uow.commit()
        return chat_id

    async def send_message(self, chat_id: str, user_id: str, content: str):
        exists = await self.user_chat_repository.verify_user_chat(chat_id=chat_id, user_id=user_id) # TODO Move to this UserService later
        if not exists:
            raise PermissionError("User is not a member of this chat or chat does not exist.")
        
        ulid_val = ULID()
        ulid_str = str(ulid_val)
        timestamp = datetime.fromtimestamp(ulid_val.timestamp, timezone.utc).isoformat()

        msg = ChatMessage(
            chat_id=chat_id,
            ulid=ulid_str,
            timestamp=timestamp,
            user_id=user_id,
            content=content
        )

        await self.chat_history_repository.create_message(msg)

        return timestamp

    async def get_chat_history(self, chat_id: str):
        messages = await self.chat_history_repository.get_chat_history(chat_id)
        return messages