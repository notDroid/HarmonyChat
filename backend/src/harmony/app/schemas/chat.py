from pydantic import BaseModel, Field

# --- API Request Models (Input) ---
class ChatCreateRequest(BaseModel):
    user_id_list: list[str] = Field(..., min_length=1, max_length=10)

class MessageSendRequest(BaseModel):
    content: str = Field(..., min_length=1)
    client_uuid: str | None = None

# --- API Response Models (Output) ---
class ChatCreatedResponse(BaseModel):
    chat_id: str

# --- Database/Internal Models (also used in responses) ---
class ChatMessage(BaseModel):
    chat_id: str
    ulid: str
    client_uuid: str | None = None
    timestamp: str
    user_id: str
    content: str

class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessage]
    next_cursor: str | None = None

class ChatDataItem(BaseModel):
    chat_id: str
    created_at: str

class UserChatItem(BaseModel):
    chat_id: str
    user_id: str