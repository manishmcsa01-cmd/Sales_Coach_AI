import uuid
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from typing import Optional
from .base import Base

class ActionRecommendation(Base):
    __tablename__ = "action_recommendations"

    id: Mapped[uuid.UUID] = mapped_column("action_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("outlets.outlet_id"))
    dsp_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("dsps.dsp_id"))
    action_type: Mapped[str]
    action_detail: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default='pending')
    completed_at: Mapped[Optional[datetime]]
    completion_notes: Mapped[Optional[str]] = mapped_column(Text)
