import uuid
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from harmony.app.models import RefreshToken 

class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_token(self, token_hash: str, user_id: uuid.UUID, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at
        )
        self.session.add(token)
        return token
    
    async def get_token(self, token_hash: str) -> RefreshToken | None:
        return await self.session.get(RefreshToken, token_hash)
    
    async def delete_token(self, token_hash: str):
        stmt = delete(RefreshToken).where(RefreshToken.token_hash == token_hash)
        await self.session.execute(stmt)