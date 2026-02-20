from harmony.app.core import settings
from harmony.app.schemas import ChatMessage
from harmony.app.db import to_dynamo_json, from_dynamo_json, paginate_in_batches
from .base_repo import BaseRepository

class ChatHistoryRepository(BaseRepository):
    table_name = settings.CHAT_HISTORY_TABLE_NAME
    
    def __init__(self, client):
        super().__init__(client)

    async def create_message(self, item: ChatMessage):
        dynamo_item = to_dynamo_json(item.model_dump())
        
        await self.writer.put_item(
            TableName=self.table_name,
            Item=dynamo_item,
            ConditionExpression='attribute_not_exists(chat_id)',
        )

    async def get_chat_history(self, chat_id: str, limit: int = 50, cursor: str | None = None):
        query_kwargs = {
            "TableName": self.table_name,
            "KeyConditionExpression": "chat_id = :cid",
            "ExpressionAttributeValues": to_dynamo_json({":cid": chat_id}),
            "Limit": limit,
            "ScanIndexForward": False # Fetches newest messages (highest ULID) first
        }
        
        if cursor:
            query_kwargs["ExclusiveStartKey"] = to_dynamo_json({"chat_id": chat_id, "ulid": cursor})
            
        response = await self.client.query(**query_kwargs)
        
        items = [from_dynamo_json(item) for item in response.get("Items", [])]
        messages = [ChatMessage.model_validate(item) for item in items]
        
        last_evaluated_key = response.get("LastEvaluatedKey")
        next_cursor = from_dynamo_json(last_evaluated_key).get("ulid") if last_evaluated_key else None
        
        return messages, next_cursor

    async def delete_chat_history(self, chat_id: str):
        async for batch in paginate_in_batches(
            client=self.client,
            query_kwargs={
                "TableName": self.table_name,
                "KeyConditionExpression": "chat_id = :cid",
                "ExpressionAttributeValues": to_dynamo_json({
                    ":cid": chat_id
                }),
                "ProjectionExpression": "chat_id, ulid"
            },
            batch_size=25,
        ):
            await self.writer.delete_batch(TableName=self.table_name, Keys=batch)