import uuid
import asyncio
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from harmony.app.core import settings
from harmony.app.repositories import UserDataRepository, UserChatRepository
from harmony.app.schemas import UserChatItem, UserSchema
from harmony.app.models import User
from pydantic import EmailStr, TypeAdapter
from ..cache import CacheService

email_adapter = TypeAdapter(EmailStr)

logger = structlog.get_logger(__name__)

class UserQueries:
    """
    Handles all read-only operations (Queries) for the User domain.
    """

    CACHE_USER_TTL_SECONDS = settings.CACHE_USER_TTL_SECONDS

    @staticmethod
    def _user_cache_key(user_id: uuid.UUID) -> str:
        return f"user:{user_id}"

    def __init__(
        self, 
        session: AsyncSession,
        user_data_repository: UserDataRepository,
        user_chat_repository: UserChatRepository,
        cache_service: CacheService | None = None
    ):
        self.session = session
        self.user_data_repo = user_data_repository
        self.user_chat_repo = user_chat_repository
        self.cache_service = cache_service

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserSchema:
        # 1. Try to fetch from cache first
        if self.cache_service:
            cache_key = self._user_cache_key(user_id)
            cached_user = await self.cache_service.get_json(cache_key)
            if cached_user:
                logger.debug("get_user_by_id_cache_hit", user_id=str(user_id))
                return UserSchema.model_validate(cached_user)
            logger.debug("get_user_by_id_cache_miss", user_id=str(user_id))

        # 2. Fetch from database
        user = await self.user_data_repo.get_user_by_id(user_id)
        if not user:
            logger.warning("get_user_not_found", user_id=str(user_id))
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist.")
        user = UserSchema.model_validate(user)
        
        # 3. Cache the result for future lookups
        if self.cache_service:
            try:
                cache_key = self._user_cache_key(user_id)
                await self.cache_service.set_json(cache_key, user.model_dump(mode="json"), expire=self.CACHE_USER_TTL_SECONDS)
                logger.debug("get_user_by_id_cache_set", user_id=str(user_id))
            except Exception as e:
                logger.exception("get_user_by_id_cache_set_failed", user_id=str(user_id))

        return user

    async def get_user_by_email(self, email: str, raw: bool = False) -> Optional[UserSchema | User]:
        # Validate email
        try:
            email_adapter.validate_python(email)
        except ValueError:
            logger.warning("get_user_by_email_invalid_format", email=email)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid email format.")
        
        user = await self.user_data_repo.get_user_by_email(email)
        if not user:
            logger.warning("get_user_by_email_not_found", email=email)
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist.")
        if raw:
            return user
        return UserSchema.model_validate(user)
    
    async def search_users_by_email(self, email_query: str, limit: int = 10) -> list[UserSchema]:
        if not email_query or len(email_query) < 2:
            return []
        users = await self.user_data_repo.search_users_by_email(email_query, limit=limit)
        return [UserSchema.model_validate(user) for user in users]

    async def check_user_exists(self, user_id: uuid.UUID) -> bool:
        """
        Checks if a user exists and is actively participating.
        Returns False if the user does not exist or if they are tombstoned.
        """
        user = await self.get_user_by_id(user_id)
        if user and user.tombstone:
            return False
        return user is not None

    async def get_user_chats(self, user_id: uuid.UUID) -> List[UserChatItem]:
        try:
            rows = await self.user_chat_repo.get_user_chats(user_id=user_id)
            return [UserChatItem(chat_id=row.chat_id, meta=row.meta) for row in rows]
        except Exception as e:
            logger.exception("get_user_chats_failed", user_id=str(user_id))
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, 
                "An unexpected error occurred while fetching user chats."
            )
        
    async def get_users_dict(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, UserSchema]:
        if not user_ids: 
            return {}

        result_dict: dict[uuid.UUID, UserSchema] = {}
        uncached_ids: list[uuid.UUID] = []

        # 1. Concurrent Cache Lookup
        if self.cache_service:
            cache_keys = [self._user_cache_key(uid) for uid in user_ids]
            
            # Fire all cache gets concurrently
            cache_results = await asyncio.gather(
                *(self.cache_service.get_json(key) for key in cache_keys),
                return_exceptions=True
            )

            # Sort out hits vs misses
            for uid, cached_data in zip(user_ids, cache_results):
                if isinstance(cached_data, dict):
                    result_dict[uid] = UserSchema.model_validate(cached_data)
                else:
                    uncached_ids.append(uid)
        else:
            uncached_ids = user_ids

        # 2. Bulk Database Fetch for Misses
        if uncached_ids:
            db_users = await self.user_data_repo.get_users_by_ids(uncached_ids)
            cache_tasks = []

            for uid, user in db_users.items():
                schema_user = UserSchema.model_validate(user)
                result_dict[uid] = schema_user

                # 3. Prepare Cache Population for Misses
                if self.cache_service:
                    cache_key = self._user_cache_key(uid)
                    cache_tasks.append(
                        self.cache_service.set_json(
                            cache_key, 
                            schema_user.model_dump(mode="json"), 
                            expire=self.CACHE_USER_TTL_SECONDS
                        )
                    )

            # Fire all cache sets concurrently in the background
            if cache_tasks:
                try:
                    await asyncio.gather(*cache_tasks)
                    logger.debug("get_users_dict_cache_populated", populated_count=len(cache_tasks))
                except Exception as e:
                    logger.exception("get_users_dict_cache_set_failed")

        return result_dict