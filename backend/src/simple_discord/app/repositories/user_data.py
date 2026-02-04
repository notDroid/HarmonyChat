from simple_discord.app.core import settings
from simple_discord.app.db import to_dynamo_json, from_dynamo_json
from simple_discord.app.schemas import UserDataItem

class UserDataRepository:
    table_name = settings.USER_DATA_TABLE_NAME
    
    def __init__(self, client):
        self.client = client

    async def create_user(self, item: UserDataItem, unit_of_work=None):
        dynamo_item = to_dynamo_json(item.model_dump())
        
        if unit_of_work:
            unit_of_work.add_operation({
                "Put": {
                    "TableName": self.table_name,
                    "Item": dynamo_item,
                    "ConditionExpression": "attribute_not_exists(user_id)"
                }
            })
        else:
            await self.client.put_item(
                TableName=self.table_name,
                Item=dynamo_item,
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
        await self.client.put_item(
            TableName=self.table_name,
            Item=to_dynamo_json(tombstone_item)
        )