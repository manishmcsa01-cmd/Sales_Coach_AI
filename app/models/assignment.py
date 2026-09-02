import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import date
from typing import Optional
from .base import Base

class DspOutletAssignment(Base):
    __tablename__ = "dsp_outlet_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dsp_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dsps.dsp_id"))
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outlets.outlet_id"))
    assigned_date: Mapped[Optional[date]]
    is_primary: Mapped[Optional[bool]] = mapped_column(default=True)
