from simple_discord.app.core import settings
from simple_discord.app.db import to_dynamo_json, from_dynamo_json, batch_request
from simple_discord.app.schemas import UserChatItem

class UserChatRepository:
    table_name = settings.USER_CHAT_TABLE_NAME
    
    def __init__(self, client):
        self.client = client

    async def create_chat(self, chat_id: str, user_id_list: list[str]):
        write_requests = [
            {
                "PutRequest": {
                    "Item": to_dynamo_json({
                        "user_id": user_id,
                        "chat_id": chat_id
                    })
                }
            }
            for user_id in user_id_list
        ]

        await batch_request(self.client, self.table_name, write_requests)

    async def verify_user_chat(self, chat_id: str, user_id: str):
        response = await self.client.get_item(
            TableName=self.table_name,
            Key=to_dynamo_json({
                "user_id": user_id,
                "chat_id": chat_id
            })
        )
        return "Item" in response