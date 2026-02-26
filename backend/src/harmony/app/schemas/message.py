import uuid
from datetime import datetime
from harmony.app.schemas.metadata import UserMetaData
from pydantic import BaseModel, Field

# Used as the message schema (is flexible)
class ChatMessage(BaseModel):
    chat_id: uuid.UUID
    ulid: str
    client_uuid: uuid.UUID | None = None
    timestamp: datetime
    user_id: uuid.UUID
    content: str

class ChatMessageResponse(ChatMessage):
    author_metadata: UserMetaData | None = None