import uuid
from pydantic import BaseModel, EmailStr, ConfigDict
from .metadata import UserMetaData

# --- API Request Models (Input) ---
class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

# --- API Response Models (Output) ---
class UserResponse(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    meta: UserMetaData
    
    model_config = ConfigDict(from_attributes=True)

class UserChatsResponse(BaseModel):
    chat_id_list: list[uuid.UUID]