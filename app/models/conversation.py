import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from typing import Optional, Any
from .base import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column("conversation_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("user_accounts.user_id"))
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    messages: Mapped[Optional[Any]] = mapped_column(JSONB)
    status: Mapped[Optional[str]]
