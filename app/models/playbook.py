import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Numeric, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class ActionCatalog(Base):
    __tablename__ = "action_catalog"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_code: Mapped[str] = mapped_column(String(64), unique=True)
    action_name: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(64))
    recommended_duration_minutes: Mapped[int] = mapped_column(Integer, default=20)
    business_impact: Mapped[str] = mapped_column(String(32), default="high")


class PitchPlaybook(Base):
    __tablename__ = "pitch_playbooks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("merchant_categories.id", ondelete="SET NULL"))
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="SET NULL"))
    merchant_objection: Mapped[str] = mapped_column(Text)
    recommended_pitch: Mapped[str] = mapped_column(Text)
    incentive_offer: Mapped[Optional[str]] = mapped_column(String(255))
    effectiveness_rating: Mapped[float] = mapped_column(Numeric(3, 2), default=4.50)


class ActionFeedbackLog(Base):
    __tablename__ = "action_feedback_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("action_recommendations.action_id", ondelete="CASCADE"))
    dsp_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dsps.dsp_id", ondelete="CASCADE"))
    is_accepted: Mapped[bool] = mapped_column(Boolean)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(64))
    feedback_notes: Mapped[Optional[str]] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
