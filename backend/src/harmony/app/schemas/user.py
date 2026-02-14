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

# --- Database/Internal Models ---
class UserMetaData(BaseModel):
    username: str
    created_at: str

class UserDataItem(BaseModel):
    user_id: str
    email: EmailStr
    tombstone: bool = False
    hashed_password: str
    metadata: UserMetaData