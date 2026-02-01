from simple_discord.app.core import settings
from simple_discord.app.db import to_dynamo_json, from_dynamo_json
from simple_discord.app.schemas import UserDataItem

class UserDataRepository:
    table_name = settings.USER_DATA_TABLE_NAME
    
    def __init__(self, client):
        self.client = client

    async def create_user(self, item: UserDataItem):
        dynamo_item = to_dynamo_json(item.model_dump())
        
        await self.client.put_item(
            TableName=self.table_name,
            Item=dynamo_item,
            ConditionExpression='attribute_not_exists(user_id)',
        )