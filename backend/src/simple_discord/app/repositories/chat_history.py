from simple_discord.app.core import settings
from simple_discord.app.schemas import ChatMessage
from simple_discord.app.db import to_dynamo_json, from_dynamo_json, process_batch

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

    async def delete_chat_history(self, chat_id: str):
        paginator = self.client.get_paginator('query')
        
        async for page in paginator.paginate(
            TableName=self.table_name,
            KeyConditionExpression="chat_id = :cid",
            ExpressionAttributeValues=to_dynamo_json({":cid": chat_id}),
            ProjectionExpression="ulid" # Only fetch the Sort Key
        ):
            batch_requests = []
            
            for item in page.get("Items", []):
                batch_requests.append({
                    "DeleteRequest": {
                        "Key": {
                            "chat_id": {"S": chat_id},
                            "ulid": item["ulid"]
                        }
                    }
                })
                
                if len(batch_requests) == 25:
                    await process_batch(self.client, self.table_name, batch_requests)
                    batch_requests = [] # Reset
            
            if batch_requests:
                await process_batch(self.client, self.table_name, batch_requests)