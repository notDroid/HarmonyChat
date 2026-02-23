from pydantic import BaseModel, Field

# Used as the message schema (is flexible)
class ChatMessage(BaseModel):
    chat_id: str
    ulid: str
    client_uuid: str | None = None
    timestamp: str
    user_id: str
    content: str