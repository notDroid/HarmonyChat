import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from .message import ChatMessageResponse
from .metadata import ChatMetaData

# --- API Request Models (Input) ---
class ChatCreateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    user_id_list: list[uuid.UUID] = Field(..., max_length=10)

class MessageSendRequest(BaseModel):
    content: str = Field(..., min_length=1)
    client_uuid: uuid.UUID | None = None

# --- API Response Models (Output) ---
class ChatResponse(BaseModel):
    chat_id: uuid.UUID
    created_at: datetime
    
    meta: ChatMetaData 
    model_config = ConfigDict(from_attributes=True)

class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
    next_cursor: str | None = None