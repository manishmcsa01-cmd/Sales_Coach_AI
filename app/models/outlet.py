import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import Optional
from .base import Base

class Outlet(Base):
    __tablename__ = "outlets"

    id: Mapped[uuid.UUID] = mapped_column("outlet_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.merchant_id"))
    outlet_name: Mapped[str]
    address: Mapped[Optional[str]]
    city: Mapped[Optional[str]]
    region: Mapped[Optional[str]]
    latitude: Mapped[Optional[float]]
    longitude: Mapped[Optional[float]]
    outlet_type: Mapped[Optional[str]]
    status: Mapped[str] = mapped_column(String(50))
    area_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("areas.area_id"))

    merchant: Mapped["Merchant"] = relationship(back_populates="outlets")
    area: Mapped[Optional["Area"]] = relationship(back_populates="outlets")
