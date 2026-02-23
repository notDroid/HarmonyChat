from sqlalchemy import select, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from harmony.app.models import Chat 

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import Any

class ChatDataRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chat(self, initial_metadata: dict[str, Any] = None) -> Chat:
        chat = Chat()
        if initial_metadata:
            chat.metadata = initial_metadata
            
        self.session.add(chat)
        return chat

    async def get_chat(self, chat_id: uuid.UUID) -> Chat | None:
        return await self.session.get(Chat, chat_id)
    
    async def update_metadata(self, chat_id: uuid.UUID, new_metadata: dict[str, Any]):
        stmt = (
            update(Chat)
            .where(Chat.chat_id == chat_id)
            .values(metadata=new_metadata)
        )
        await self.session.execute(stmt)

    async def delete_chat(self, chat_id: uuid.UUID):
        stmt = delete(Chat).where(Chat.chat_id == chat_id)
        await self.session.execute(stmt)