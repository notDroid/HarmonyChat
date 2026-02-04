from pydantic import BaseModel
from .db import ChatMessage, UserMetaData

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

# Create User
CreateUserRequest = UserMetaData  # Alias for clarity in API schema

class CreateUserResponse(BaseModel):
    user_id: str

class GetUserChatsResponse(BaseModel):
    chat_id_list: list[str]