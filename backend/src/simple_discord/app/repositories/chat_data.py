from simple_discord.app.core import settings
from simple_discord.app.db import to_dynamo_json, from_dynamo_json
from simple_discord.app.schemas import ChatDataItem

class ChatDataRepository:
    table_name = settings.CHAT_DATA_TABLE_NAME
    
    def __init__(self, client):
        self.client = client

    async def create_chat(self, item: ChatDataItem, unit_of_work=None):
        dynamo_item = to_dynamo_json(item.model_dump())
        
        if unit_of_work:
            unit_of_work.add_operation({
                "Put": {
                    "TableName": self.table_name,
                    "Item": dynamo_item,
                    "ConditionExpression": "attribute_not_exists(chat_id)"
                }
            })
        else:
            await self.client.put_item(
                TableName=self.table_name,
                Item=dynamo_item,
                ConditionExpression='attribute_not_exists(chat_id)',
            )

    async def get_chat_by_id(self, chat_id: str) -> ChatDataItem | None:
        response = await self.client.get_item(
            TableName=self.table_name,
            Key=to_dynamo_json({"chat_id": chat_id})
        )
        item = response.get("Item")
        if not item:
            return None
        chat_data = from_dynamo_json(item)
        return ChatDataItem.model_validate(chat_data)
    
    async def chat_exists(self, chat_id: str) -> bool:
        response = await self.client.get_item(
            TableName=self.table_name,
            Key=to_dynamo_json({"chat_id": chat_id}),
            ProjectionExpression="chat_id"
        )
        return "Item" in response
    
    async def delete_chat(self, chat_id: str, unit_of_work=None):
        if unit_of_work:
            unit_of_work.add_operation({
                "Delete": {
                    "TableName": self.table_name,
                    "Key": to_dynamo_json({
                        "chat_id": chat_id
                    })
                }
            })
        else:
            await self.client.delete_item(
                TableName=self.table_name,
                Key=to_dynamo_json({
                    "chat_id": chat_id
                })
        )