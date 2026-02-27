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

    async def consume_token(self, token_hash: str) -> RefreshToken:
        stmt = (
            delete(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .returning(RefreshToken)
        )
        
        result = await self.session.execute(stmt)
        deleted_token = result.scalar_one_or_none()

        if not deleted_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token."
            )
            
        return deleted_token