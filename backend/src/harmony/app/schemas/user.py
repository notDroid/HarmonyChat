from pydantic import BaseModel, EmailStr

class UserMetaData(BaseModel):
    username: str
    created_at: str

class UserDataItem(BaseModel):
    user_id: str
    email: EmailStr
    tombstone: bool
    hashed_password: str
    metadata: UserMetaData

class UserCreate(BaseModel):
    username: str | None = None
    email: EmailStr
    password: str
    hashed_password: str | None = None