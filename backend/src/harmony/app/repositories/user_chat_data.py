import uuid
from typing import List
from sqlalchemy import select, delete, exists, insert
from sqlalchemy.ext.asyncio import AsyncSession

from harmony.app.models import UserChat, Chat

class UserChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_users_to_chat(self, chat_id: uuid.UUID, user_id_list: List[uuid.UUID]):
        if not user_id_list:
            raise ValueError("user_id_list cannot be empty")
            
        stmt = insert(UserChat).values([
            {"chat_id": chat_id, "user_id": uid} for uid in user_id_list
        ])
        await self.session.execute(stmt)

    async def remove_user_from_chat(self, chat_id: uuid.UUID, user_id: uuid.UUID):
        stmt = (
            delete(UserChat)
            .where(UserChat.chat_id == chat_id, UserChat.user_id == user_id)
        )
        await self.session.execute(stmt)

    async def check_user_in_chat(self, chat_id: uuid.UUID, user_id: uuid.UUID, lock: bool = False) -> bool:
        stmt = select(UserChat.user_id).where(
            UserChat.chat_id == chat_id, 
            UserChat.user_id == user_id
        )
        if lock:
            stmt = stmt.with_for_update(read=True)

        result = await self.session.execute(stmt)
        return result.first() is not None

    async def get_user_chats(self, user_id: uuid.UUID) -> List[uuid.UUID]:
        stmt = (
            select(Chat.chat_id, Chat.meta)
            .join(UserChat, UserChat.chat_id == Chat.chat_id)
            .where(UserChat.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.all()
    
    async def get_chat_users(self, chat_id: uuid.UUID) -> List[uuid.UUID]:
        stmt = select(UserChat.user_id).where(UserChat.chat_id == chat_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())