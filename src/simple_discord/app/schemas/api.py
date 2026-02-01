from pydantic import BaseModel
from .db import ChatMessage

# Send Message
class SendMessageRequest(BaseModel):
    user_id: str
    content: str

class SendMessageResponse(BaseModel):
    status: str
    timestamp: str

# Get Chat History
class GetChatHistoryResponse(BaseModel):
    messages: list[ChatMessage]

# Create Chat
class CreateChatRequest(BaseModel):
    user_id_list: list[str]

class CreateChatResponse(BaseModel):
    chat_id: str