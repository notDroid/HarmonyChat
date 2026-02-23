from pydantic import BaseModel, Field
from .message import ChatMessage

# --- API Request Models (Input) ---
class ChatCreateRequest(BaseModel):
    user_id_list: list[str] = Field(..., min_length=1, max_length=10)

class MessageSendRequest(BaseModel):
    content: str = Field(..., min_length=1)
    client_uuid: str | None = None

# --- API Response Models (Output) ---
class ChatCreatedResponse(BaseModel):
    chat_id: str

class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessage]
    next_cursor: str | None = None