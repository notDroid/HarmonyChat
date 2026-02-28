from sqlalchemy import text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

import uuid
from datetime import datetime
from typing import List, Any

from .base import Base


class Chat(Base):
    __tablename__ = "chats"
    
    chat_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        server_default=text("gen_random_uuid()")
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    meta: Mapped[dict[str, Any]] = mapped_column(
        JSONB, 
        server_default=text("'{}'::jsonb")
    )

    users: Mapped[List["User"]] = relationship(
        secondary="user_chats", 
        back_populates="chats"
    )