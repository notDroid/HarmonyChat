from harmony.app.core import settings
from harmony.app.db import to_dynamo_json, from_dynamo_json
from harmony.app.schemas import UserDataItem
from .base_repo import BaseRepository

class UserDataRepository(BaseRepository):
    table_name = settings.USER_DATA_TABLE_NAME
    
    def __init__(self, client):
        super().__init__(client)

    async def create_user(self, item: UserDataItem):
        await self.writer.put_item(
            TableName=self.table_name,
            Item=to_dynamo_json(item.model_dump()),
            ConditionExpression='attribute_not_exists(user_id)',
        )

    async def get_user_by_id(self, user_id: str) -> UserDataItem | None:
        response = await self.client.get_item(
            TableName=self.table_name,
            Key=to_dynamo_json({"user_id": user_id})
        )
        item = response.get("Item")
        if not item:
            return None
        user_data = from_dynamo_json(item)
        return UserDataItem.model_validate(user_data)

    async def make_user_tombstone(self, user_id: str):
        tombstone_item = {
            "user_id": user_id,
            "tombstone": True
        }
        await self.writer.put_item(
            TableName=self.table_name,
            Item=to_dynamo_json(tombstone_item),
            ConditionExpression='attribute_not_exists(user_id)',
        )