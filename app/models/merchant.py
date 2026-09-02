from sqlalchemy import String
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import Optional
from datetime import date
from .base import Base

class Merchant(Base):
    __tablename__ = "merchants"

    # Override id to use merchant_id as the column name if needed, but the prompt says 
    # to use base with id. We'll map the primary key carefully.
    id: Mapped[uuid.UUID] = mapped_column("merchant_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_name: Mapped[str]
    owner_name: Mapped[Optional[str]]
    business_type: Mapped[Optional[str]] = mapped_column(String(50))
    kyc_status: Mapped[Optional[str]]
    onboarded_date: Mapped[Optional[date]]
    risk_tier: Mapped[Optional[str]]

    outlets: Mapped[list["Outlet"]] = relationship(back_populates="merchant")
