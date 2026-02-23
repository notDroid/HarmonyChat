import uuid
from pydantic import BaseModel, Field, ConfigDict
from .message import ChatMessage
from .metadata import ChatMetaData

# --- API Request Models (Input) ---
class ChatCreateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    user_id_list: list[uuid.UUID] = Field(..., min_length=1, max_length=10)

class MessageSendRequest(BaseModel):
    content: str = Field(..., min_length=1)
    client_uuid: str | None = None

# --- API Response Models (Output) ---
class ChatResponse(BaseModel):
    chat_id: str
    created_at: str
    
    meta: ChatMetaData 
    model_config = ConfigDict(from_attributes=True)

class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessage]
    next_cursor: str | None = None