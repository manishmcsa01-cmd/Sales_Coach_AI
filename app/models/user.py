import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from typing import Optional
from .base import Base

class UserAccount(Base):
    __tablename__ = "user_accounts"

    id: Mapped[uuid.UUID] = mapped_column("user_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    role: Mapped[str]
    linked_dsp_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("dsps.dsp_id"))
    status: Mapped[Optional[str]]
    last_login: Mapped[Optional[datetime]]

    # Example methods for password
    def set_password(self, pwd: str):
        # implementation using passlib/bcrypt
        pass
    
    def check_password(self, pwd: str) -> bool:
        # implementation using passlib/bcrypt
        return False
