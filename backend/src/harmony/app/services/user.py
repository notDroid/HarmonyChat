from harmony.app.db import UnitOfWorkFactory
from harmony.app.repositories import UserChatRepository, UserDataRepository, EmailSetRepository
from harmony.app.schemas import UserDataItem, UserMetaData, UserCreateRequest

from ulid import ULID
from datetime import datetime, timezone

class UserService:
    
    def __init__(
            self,
            user_chat_repository: UserChatRepository, 
            user_data_repository: UserDataRepository,
            email_set_repository: EmailSetRepository,
            unit_of_work: UnitOfWorkFactory
    ):
        self.user_chat_repository = user_chat_repository
        self.user_data_repository = user_data_repository
        self.email_set_repository = email_set_repository
        self.uow_factory = unit_of_work

    async def get_user_by_id(self, user_id: str) -> UserDataItem | None:
        return await self.user_data_repository.get_user_by_id(user_id)
    
    async def check_user_exists(self, user_id: str) -> bool:
        user_data =  await self.user_data_repository.get_user_by_id(user_id)
        if user_data and getattr(user_data, "tombstone", False):
            return False
        return user_data is not None
    
    async def create_user(self, req: UserCreateRequest):
        ulid_val = ULID()
        user_id = str(ulid_val)
        timestamp = datetime.fromtimestamp(ulid_val.timestamp, timezone.utc).isoformat()
        user_metadata = UserMetaData(
            username=req.username if req.username else user_id,
            created_at=timestamp
        )

        user_data_item = UserDataItem(
            user_id=user_id,
            tombstone=False,
            email=req.email,
            hashed_password=req.hashed_password,
            metadata=user_metadata
        )

        async with self.uow_factory() as uow:
            await self.email_set_repository.add_email(req.email)
            await self.user_data_repository.create_user(user_data_item)
            await uow.commit()
        return user_id

    async def delete_user(self, user_id: str):
        await self.user_data_repository.make_user_tombstone(user_id) 
        # Never delete users, later we could make a revive user function where the user must sign up again with the same email.

    async def get_user_chats(self, user_id: str) -> list[str]: 
        chat_id_list = await self.user_chat_repository.get_user_chats(user_id=user_id)
        return chat_id_list
    
    async def get_user_by_email(self, email: str) -> UserDataItem | None:
        return await self.user_data_repository.get_user_by_email(email)