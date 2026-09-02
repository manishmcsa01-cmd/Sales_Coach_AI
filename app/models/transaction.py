from typing import Optional
import uuid
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from .base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column("txn_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outlets.outlet_id"))
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("products.product_id"))
    txn_type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Numeric)
    txn_date: Mapped[datetime]
    status: Mapped[str]
