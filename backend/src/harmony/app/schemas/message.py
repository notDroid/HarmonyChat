import uuid
from datetime import datetime
from pydantic import BaseModel, Field

# Used as the message schema (is flexible)
class ChatMessage(BaseModel):
    chat_id: uuid.UUID
    ulid: str
    client_uuid: uuid.UUID | None = None
    timestamp: datetime
    user_id: uuid.UUID
    content: str