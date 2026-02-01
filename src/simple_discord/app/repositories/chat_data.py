from simple_discord.app.core import settings
from simple_discord.app.db import to_dynamo_json, from_dynamo_json
from simple_discord.app.schemas import ChatDataItem

class ChatDataRepository:
    table_name = settings.CHAT_DATA_TABLE_NAME
    
    def __init__(self, client):
        self.client = client

    async def create_chat(self, item: ChatDataItem):
        dynamo_item = to_dynamo_json(item.model_dump())
        
        await self.client.put_item(
            TableName=self.table_name,
            Item=dynamo_item,
            ConditionExpression='attribute_not_exists(chat_id)',
        )
    
    async def delete_chat(self, chat_id: str):
        await self.client.delete_item(
            TableName=self.table_name,
            Key=to_dynamo_json({
                "chat_id": chat_id
            })
        )