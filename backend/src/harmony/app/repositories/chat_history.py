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
            
    # TODO: Switch to a paginated approach
    async def get_chat_history(self, chat_id: str):
        response = await self.client.query(
            TableName=self.table_name,
            KeyConditionExpression="chat_id = :cid",
            ExpressionAttributeValues=to_dynamo_json({":cid": chat_id}),
        )
        
        items = [from_dynamo_json(item) for item in response.get("Items", [])]
        return [ChatMessage.model_validate(item) for item in items]

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