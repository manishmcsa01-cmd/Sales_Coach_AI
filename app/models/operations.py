import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import ForeignKey, String, Numeric, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Distributor(Base):
    __tablename__ = "distributors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(255))
    tax_id: Mapped[Optional[str]] = mapped_column(String(64))
    contact_person: Mapped[Optional[str]] = mapped_column(String(128))
    contact_email: Mapped[Optional[str]] = mapped_column(String(128))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="active")


class Manager(Base):
    __tablename__ = "managers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(128), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64))
    area_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("areas.area_id"))
    distributor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("distributors.id"))
    status: Mapped[str] = mapped_column(String(32), default="active")
    hire_date: Mapped[Optional[date]]


class PosTerminal(Base):
    __tablename__ = "pos_terminals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outlets.outlet_id", ondelete="CASCADE"))
    terminal_sn: Mapped[str] = mapped_column(String(64), unique=True)
    device_model: Mapped[str] = mapped_column(String(64))
    firmware_version: Mapped[Optional[str]] = mapped_column(String(64))
    battery_health_pct: Mapped[int] = mapped_column(Integer, default=100)
    connectivity_type: Mapped[str] = mapped_column(String(32), default="4G_LTE")
    hardware_status: Mapped[str] = mapped_column(String(32), default="operational")
    last_heartbeat: Mapped[Optional[datetime]]


class QrCollateral(Base):
    __tablename__ = "qr_collaterals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outlets.outlet_id", ondelete="CASCADE"))
    collateral_type: Mapped[str] = mapped_column(String(64))
    qr_payload_version: Mapped[str] = mapped_column(String(32), default="QRPh-v2")
    qr_code_id: Mapped[str] = mapped_column(String(128))
    condition: Mapped[str] = mapped_column(String(32), default="good")
    placement_location: Mapped[str] = mapped_column(String(64), default="counter_checkout")
    deployed_at: Mapped[Optional[date]]
    last_inspected_at: Mapped[Optional[date]]


class OperatingHours(Base):
    __tablename__ = "outlet_operating_hours"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outlets.outlet_id", ondelete="CASCADE"))
    day_of_week: Mapped[int] = mapped_column(Integer)
    opening_time: Mapped[str] = mapped_column(String(16))
    closing_time: Mapped[str] = mapped_column(String(16))
    peak_traffic_window: Mapped[Optional[str]] = mapped_column(String(64))
    is_24_hours: Mapped[bool] = mapped_column(Boolean, default=False)
