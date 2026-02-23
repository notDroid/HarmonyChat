import uuid
from typing import Any, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from harmony.app.models import User 

class UserDataRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, email: str, hashed_password: str, metadata: dict[str, Any] = None) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            metadata=metadata or {}
        )
        self.session.add(user)
        return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def make_user_tombstone(self, user_id: uuid.UUID):
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(tombstone=True)
        )
        await self.session.execute(stmt)