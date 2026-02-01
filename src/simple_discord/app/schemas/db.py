from pydantic import BaseModel


class ChatHistoryItem(BaseModel):
    chat_id: str
    ulid: str
    timestamp: str
    user_id: str
    content: str
ChatMessage = ChatHistoryItem  # Alias for clarity in API schema

class ChatDataItem(BaseModel):
    chat_id: str
    created_at: str
    state: str # one of 'valid', 'deleted'

class UserChatItem(BaseModel): # Unused but kept for reference
    chat_id: str
    user_id: str

class UserDataItem(BaseModel):
    user_id: str
    username: str