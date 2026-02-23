from pydantic import BaseModel, EmailStr, Field

# --- Shared Properties ---
class UserBase(BaseModel):
    username: str
    email: EmailStr

# --- API Request Models (Input) ---
class UserCreateRequest(UserBase):
    password: str

# --- API Response Models (Output) ---
class UserResponse(BaseModel):
    user_id: str

class UserChatsResponse(BaseModel):
    chat_id_list: list[str]