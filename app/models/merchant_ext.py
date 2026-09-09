import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import ForeignKey, String, Numeric, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class MerchantCategory(Base):
    __tablename__ = "merchant_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_code: Mapped[str] = mapped_column(String(64), unique=True)
    category_name: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(Text)
    benchmark_monthly_txns: Mapped[int] = mapped_column(Integer, default=500)
    default_cash_in_fee_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.0100)


class MerchantKycDocument(Base):
    __tablename__ = "merchant_kyc_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.merchant_id", ondelete="CASCADE"))
    document_type: Mapped[str] = mapped_column(String(64))
    document_number: Mapped[str] = mapped_column(String(128))
    verification_status: Mapped[str] = mapped_column(String(32), default="approved")
    verified_at: Mapped[Optional[datetime]]
    expires_at: Mapped[Optional[date]]


class MerchantBankAccount(Base):
    __tablename__ = "merchant_bank_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.merchant_id", ondelete="CASCADE"))
    bank_name: Mapped[str] = mapped_column(String(128))
    account_number_mask: Mapped[str] = mapped_column(String(64))
    account_type: Mapped[str] = mapped_column(String(32), default="savings")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(32), default="active")


class MerchantContact(Base):
    __tablename__ = "merchant_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.merchant_id", ondelete="CASCADE"))
    contact_name: Mapped[str] = mapped_column(String(128))
    contact_role: Mapped[str] = mapped_column(String(64))
    phone_number: Mapped[str] = mapped_column(String(64))
    email: Mapped[Optional[str]] = mapped_column(String(128))
    is_primary_decision_maker: Mapped[bool] = mapped_column(Boolean, default=False)
