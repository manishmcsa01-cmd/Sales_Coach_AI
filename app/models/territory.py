import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Region(Base):
    __tablename__ = "regions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_code: Mapped[str] = mapped_column(String(32), unique=True)
    region_name: Mapped[str] = mapped_column(String(128))
    island_group: Mapped[str] = mapped_column(String(32))

    provinces: Mapped[list["Province"]] = relationship(back_populates="region", cascade="all, delete-orphan")


class Province(Base):
    __tablename__ = "provinces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id", ondelete="CASCADE"))
    province_name: Mapped[str] = mapped_column(String(128))
    province_code: Mapped[str] = mapped_column(String(32), unique=True)

    region: Mapped["Region"] = relationship(back_populates="provinces")
    cities: Mapped[list["CityMunicipality"]] = relationship(back_populates="province", cascade="all, delete-orphan")


class CityMunicipality(Base):
    __tablename__ = "cities_municipalities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    province_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("provinces.id", ondelete="CASCADE"))
    city_name: Mapped[str] = mapped_column(String(128))
    postal_code: Mapped[Optional[str]] = mapped_column(String(16))
    urban_tier: Mapped[str] = mapped_column(String(32), default="Metro_Tier1")

    province: Mapped["Province"] = relationship(back_populates="cities")
