import uuid
from pydantic import BaseModel, EmailStr, ConfigDict
from .metadata import ChatMetaData, UserMetaData

# --- API Request Models (Input) ---
class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

# --- API Response Models (Output) ---
class UserSchema(BaseModel): # Synced with User SQLAlchemy model
    user_id: uuid.UUID
    email: EmailStr
    meta: UserMetaData
    
    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserSchema):
    pass

class UserChatItem(BaseModel):
    chat_id: uuid.UUID
    meta: ChatMetaData  # A different approach may only fetch minimal metadata (e.g. title) and fetch the rest when the user clicks into the chat.

class UserChatsResponse(BaseModel):
    chats: list[UserChatItem]