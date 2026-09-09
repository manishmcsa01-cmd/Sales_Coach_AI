import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import ForeignKey, String, Numeric, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("user_accounts.user_id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(64))
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[Optional[str]] = mapped_column(String(128))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class MerchandisingAuditItem(Base):
    __tablename__ = "merchandising_audit_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("visit_logs.visit_id", ondelete="CASCADE"))
    collateral_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("qr_collaterals.id", ondelete="SET NULL"))
    audit_category: Mapped[str] = mapped_column(String(64))
    is_compliant: Mapped[bool] = mapped_column(Boolean)
    deficiency_reason: Mapped[Optional[str]] = mapped_column(String(64))
    action_taken: Mapped[Optional[str]] = mapped_column(String(64))


class OutletPhoto(Base):
    __tablename__ = "outlet_photos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("visit_logs.visit_id", ondelete="CASCADE"))
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outlets.outlet_id", ondelete="CASCADE"))
    photo_type: Mapped[str] = mapped_column(String(64))
    photo_url: Mapped[str] = mapped_column(String(512))
    ai_validation_label: Mapped[Optional[str]] = mapped_column(String(64))
    ai_confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    captured_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class DailyOutletMetric(Base):
    __tablename__ = "daily_outlet_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outlets.outlet_id", ondelete="CASCADE"))
    metric_date: Mapped[date]
    total_gmv: Mapped[float] = mapped_column(Numeric(15, 2), default=0.00)
    total_transactions: Mapped[int] = mapped_column(Integer, default=0)
    failed_transactions: Mapped[int] = mapped_column(Integer, default=0)
    unique_customers: Mapped[int] = mapped_column(Integer, default=0)
    avg_ticket_size: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    cash_in_volume: Mapped[float] = mapped_column(Numeric(15, 2), default=0.00)
    qr_payment_volume: Mapped[float] = mapped_column(Numeric(15, 2), default=0.00)


class CashInLiquidityLog(Base):
    __tablename__ = "cash_in_liquidity_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outlets.outlet_id", ondelete="CASCADE"))
    log_date: Mapped[date]
    opening_float: Mapped[float] = mapped_column(Numeric(12, 2))
    closing_float: Mapped[float] = mapped_column(Numeric(12, 2))
    float_stockout_occurred: Mapped[bool] = mapped_column(Boolean, default=False)
    replenishment_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00)
    replenishment_source: Mapped[str] = mapped_column(String(64), default="none")
