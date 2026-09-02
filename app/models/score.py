import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import date
from typing import Optional, Any
from .base import Base

class OutletScore(Base):
    __tablename__ = "outlet_scores"

    id: Mapped[uuid.UUID] = mapped_column("score_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outlets.outlet_id"))
    priority_score: Mapped[float]
    contributing_factors: Mapped[Optional[Any]] = mapped_column(JSONB)
    score_date: Mapped[date]
    model_version: Mapped[Optional[str]]
