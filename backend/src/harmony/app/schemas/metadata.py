from pydantic import BaseModel, Field

# Stored as JSONB in the database (is flexible)
class UserMetaData(BaseModel):
    username: str

class ChatMetaData(BaseModel):
    title: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)