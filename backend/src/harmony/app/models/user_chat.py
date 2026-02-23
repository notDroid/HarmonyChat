from sqlalchemy import text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

import uuid
from datetime import datetime
from typing import List, Any

from .base import Base

class UserChat(Base):
    __tablename__ = "user_chats"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.chat_id"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now())