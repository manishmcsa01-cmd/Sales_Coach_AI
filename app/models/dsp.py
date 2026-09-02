import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import Optional
from datetime import date
from .base import Base

class Dsp(Base):
    __tablename__ = "dsps"
    # Using dsp_id as pk instead of id but Base provides id. Let's map it.
    id: Mapped[uuid.UUID] = mapped_column("dsp_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    role: Mapped[str] = mapped_column(String(50))
    area_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("areas.area_id"))
    manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("dsps.dsp_id"))
    hire_date: Mapped[Optional[date]]
    status: Mapped[str]

    area: Mapped[Optional["Area"]] = relationship(back_populates="dsps", foreign_keys=[area_id])
    manager: Mapped[Optional["Dsp"]] = relationship(remote_side=[id])
