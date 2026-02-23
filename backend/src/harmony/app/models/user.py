from sqlalchemy import Boolean, text, func, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

import uuid
from datetime import datetime
from typing import List, Any


from .base import Base

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        server_default=text("gen_random_uuid()")
    )
    
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )
    tombstone: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

    meta: Mapped[dict[str, Any]] = mapped_column(
        JSONB, 
        server_default=text("'{}'::jsonb")
    )

    chats: Mapped[List["Chat"]] = relationship(
        secondary="user_chats", 
        back_populates="users"
    )