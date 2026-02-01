from ulid import ULID
from datetime import datetime, timezone

from simple_discord.app.schemas import *
from simple_discord.app.repositories import ChatHistoryRepository, UserChatRepository, ChatDataRepository


class ChatService:
    def __init__(self, chat_history_repository: ChatHistoryRepository, user_chat_repository: UserChatRepository, chat_data_repository: ChatDataRepository):
        self.chat_history_repository = chat_history_repository
        self.user_chat_repository = user_chat_repository
        self.chat_data_repository = chat_data_repository

    async def create_chat(self, user_id_list: list[str]) -> str:
        if len(user_id_list) < 2:
            raise ValueError("A chat must have at least two users.")
        
        chat_id = str(ULID())
        
        chat_data_item = ChatDataItem(
            chat_id=chat_id,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        # Switch to using a transaction tomorrow to avoid partial failures
        await self.chat_data_repository.create_chat(chat_data_item)
        try:
            await self.user_chat_repository.create_chat(chat_id=chat_id, user_id_list=user_id_list)
        except Exception:
            # Rollback chat_data creation if user_chat creation fails
            await self.chat_data_repository.delete_chat(chat_id)
            raise
        return chat_id

    async def send_message(self, chat_id: str, user_id: str, content: str):
        exists = await self.user_chat_repository.verify_user_chat(chat_id=chat_id, user_id=user_id)
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