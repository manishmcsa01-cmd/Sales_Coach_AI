import uuid
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import Optional
from .base import Base

class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column("product_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_name: Mapped[str]
    category: Mapped[Optional[str]]
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
