from ulid import ULID
from datetime import datetime, timezone
from fastapi import HTTPException, status
from harmony.app.schemas import *
from harmony.app.repositories import ChatHistoryRepository, UserChatRepository, ChatDataRepository
from harmony.app.db import UnitOfWorkFactory
from .user import UserService

import asyncio

MAX_USERS_PER_OPERATION = 10

class ChatService:
    '''
    Handles chat-related operations including chat creation, message sending, and chat history retrieval.
    '''

    def __init__(
            self, 
            chat_history_repository: ChatHistoryRepository, 
            user_chat_repository: UserChatRepository, 
            chat_data_repository: ChatDataRepository,
            user_service: UserService,
            unit_of_work: UnitOfWorkFactory
        ):
        self.chat_history_repository = chat_history_repository
        self.user_chat_repository = user_chat_repository
        self.chat_data_repository = chat_data_repository
        self.user_service = user_service
        self.uow_factory = unit_of_work

    async def check_user_in_chat(self, user_id: str, chat_id: str) -> bool | None:
        '''
        Verifies that a user is a member of a chat. 
        Used where eventual consistency is acceptable, such as sending messages or retrieving history.

        This method performs two concurrent checks:
            1. Verifies the user is in the chat via UserChatRepository.
            2. Verifies the chat exists via ChatDataRepository.
        '''
        task1 = self.user_chat_repository.check_user_in_chat(user_id=user_id, chat_id=chat_id)
        task2 = self.chat_data_repository.check_chat_exists(chat_id)

        user_in_chat, chat_exists = await asyncio.gather(task1, task2)

        if not chat_exists:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat does not exist.")
        if not user_in_chat:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "User is not a member of this chat.")

    async def create_chat(self, user_id: str, user_id_list: list[str]) -> str:
        '''
        Creates a new chat with a list of user IDs. The creator is automatically added to the chat.
            Validations:
                - A chat cannot be created with more than 10 users (including the creator).
                - All user IDs must correspond to existing users.

        The users and chat are created in a single transaction to ensure consistency. More users can be added later if needed.
        '''
        user_id_list = list(set(user_id_list + [user_id]))  # Ensure the creator is included and remove duplicates
        if len(user_id_list) > MAX_USERS_PER_OPERATION:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"A chat cannot be created with more than {MAX_USERS_PER_OPERATION} users (add them later).")
        
        # Verify all users exist
        task_list = [self.user_service.check_user_exists(user_id) for user_id in user_id_list]
        user_exists = await asyncio.gather(*task_list)
        for user_id, exists in zip(user_id_list, user_exists):
            if not exists:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"User {user_id} does not exist.")
        
        # Create chat item
        ulid_val = ULID()
        chat_id = str(ulid_val)
        timestamp = datetime.fromtimestamp(ulid_val.timestamp, timezone.utc).isoformat()
        
        chat_data_item = ChatDataItem(
            chat_id=chat_id,
            created_at=timestamp
        )

        try: 
            async with self.uow_factory() as uow:
                await self.chat_data_repository.create_chat(chat_data_item)
                await self.user_chat_repository.add_users_to_chat(chat_id=chat_id, user_id_list=user_id_list)
                await uow.commit()
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to create chat: {str(e)}")
        return chat_id
    
    async def add_users_to_chat(self, user_id: str, chat_id: str, user_id_list: list[str]):
        '''
        Similar to create_chat, but for adding users to an existing chat. 
        Validations are the same, except the chat must already exist and the requesting user must be a member of the chat.
        '''

        user_id_list = list(set(user_id_list))  # Remove duplicates
        if len(user_id_list) > MAX_USERS_PER_OPERATION:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Cannot add more than {MAX_USERS_PER_OPERATION} users at once.")
        if len(user_id_list) == 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No users provided to add.")
        
        # Verify all users exist
        task_list = [self.user_service.check_user_exists(user_id) for user_id in user_id_list]
        user_exists = await asyncio.gather(*task_list)
        for user_id, exists in zip(user_id_list, user_exists):
            if not exists:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"User {user_id} does not exist.")
        
        async with self.uow_factory() as uow:
            await self.chat_data_repository.require_chat_exists(chat_id)
            await self.user_chat_repository.require_user_in_chat(chat_id, user_id)
            await self.user_chat_repository.add_users_to_chat(chat_id=chat_id, user_id_list=user_id_list)
            await uow.commit()

    async def send_message(self, chat_id: str, user_id: str, content: str):
        # Verify user is in chat
        await self.check_user_in_chat(user_id, chat_id)
        
        # Create message item
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

        return msg

    async def get_chat_history(self, user_id: str, chat_id: str) -> list[ChatMessage]:
        await self.check_user_in_chat(user_id, chat_id)
        messages = await self.chat_history_repository.get_chat_history(chat_id)
        return messages
    
    async def leave_chat(self, user_id: str, chat_id: str):
        async with self.uow_factory() as uow:
            await self.chat_data_repository.require_chat_exists(chat_id)
            await self.user_chat_repository.require_user_in_chat(chat_id, user_id)
            await self.user_chat_repository.remove_user_from_chat(chat_id=chat_id, user_id=user_id)
            await uow.commit()
    
    async def delete_chat(self, user_id: str, chat_id: str):
        async with self.uow_factory() as uow:
            await self.chat_data_repository.require_chat_exists(chat_id)
            await self.user_chat_repository.require_user_in_chat(user_id, chat_id)
            await self.chat_data_repository.delete_chat(chat_id)
            await uow.commit()

    async def background_delete_chat_history(self, chat_id: str):
        await asyncio.gather(
            self.chat_history_repository.delete_chat_history(chat_id),
            self.user_chat_repository.delete_chat(chat_id)
        )        