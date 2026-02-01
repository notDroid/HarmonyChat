from simple_discord.app.core import settings
from simple_discord.app.schemas import ChatMessage
from simple_discord.app.db import to_dynamo_json, from_dynamo_json

class ChatHistoryRepository:
    table_name = settings.CHAT_HISTORY_TABLE_NAME
    
    def __init__(self, client):
        self.client = client

    async def create_message(self, item: ChatMessage):
        dynamo_item = to_dynamo_json(item.model_dump())
        
        await self.client.put_item(
            TableName=self.table_name,
            Item=dynamo_item,
            ConditionExpression='attribute_not_exists(chat_id)',
        )
            
    async def get_chat_history(self, chat_id: str):
        response = await self.client.query(
            TableName=self.table_name,
            KeyConditionExpression="chat_id = :cid",
            ExpressionAttributeValues=to_dynamo_json({":cid": chat_id}),
        )
        
        items = [from_dynamo_json(item) for item in response.get("Items", [])]
        return [ChatMessage.model_validate(item) for item in items]
    