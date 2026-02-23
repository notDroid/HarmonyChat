from pydantic import BaseModel, Field

# Stored as JSONB in the database (is flexible)
class UserMetaData(BaseModel):
    username: str

class ChatMetaData(BaseModel):
    title: str | None = None
    description: str | None = None