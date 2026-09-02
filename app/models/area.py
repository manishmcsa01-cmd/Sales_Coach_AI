import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import Optional
from .base import Base

class Area(Base):
    __tablename__ = "areas"

    id: Mapped[uuid.UUID] = mapped_column("area_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    area_name: Mapped[str]
    region: Mapped[str]
    manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("dsps.dsp_id"))

    dsps: Mapped[list["Dsp"]] = relationship(back_populates="area", foreign_keys="[Dsp.area_id]")
    outlets: Mapped[list["Outlet"]] = relationship(back_populates="area")
