import uuid
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from typing import Optional
from .base import Base

class VisitLog(Base):
    __tablename__ = "visit_logs"

    id: Mapped[uuid.UUID] = mapped_column("visit_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dsp_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("dsps.dsp_id"))
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outlets.outlet_id"))
    visit_date: Mapped[datetime]
    visit_type: Mapped[Optional[str]]
    outcome: Mapped[Optional[str]]
    notes: Mapped[Optional[str]] = mapped_column(Text)
    duration_minutes: Mapped[Optional[int]]
