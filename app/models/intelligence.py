import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Numeric, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class ScoringFeatureStore(Base):
    __tablename__ = "scoring_feature_store"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outlet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("outlets.outlet_id", ondelete="CASCADE"))
    days_since_last_txn: Mapped[int] = mapped_column(Integer, default=0)
    days_since_last_visit: Mapped[int] = mapped_column(Integer, default=0)
    gmv_wow_growth_pct: Mapped[float] = mapped_column(Numeric(6, 2), default=0.00)
    gmv_mom_growth_pct: Mapped[float] = mapped_column(Numeric(6, 2), default=0.00)
    cash_in_stockout_count_7d: Mapped[int] = mapped_column(Integer, default=0)
    qr_standee_damage_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    pos_terminal_offline_hours_7d: Mapped[float] = mapped_column(Numeric(6, 2), default=0.00)
    computed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class MlModelRegistry(Base):
    __tablename__ = "ml_model_registry"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(128))
    model_version: Mapped[str] = mapped_column(String(32), unique=True)
    algorithm: Mapped[str] = mapped_column(String(64))
    auc_roc: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    f1_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    hyperparameters: Mapped[Optional[str]] = mapped_column(Text)
    deployment_status: Mapped[str] = mapped_column(String(32), default="champion")
    deployed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    drift_metrics: Mapped[list["ModelDriftMetric"]] = relationship(back_populates="model", cascade="all, delete-orphan")


class ModelDriftMetric(Base):
    __tablename__ = "model_drift_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ml_model_registry.id", ondelete="CASCADE"))
    feature_name: Mapped[str] = mapped_column(String(128))
    metric_type: Mapped[str] = mapped_column(String(32))
    metric_value: Mapped[float] = mapped_column(Numeric(8, 4))
    threshold: Mapped[float] = mapped_column(Numeric(8, 4), default=0.2000)
    drift_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    evaluated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    model: Mapped["MlModelRegistry"] = relationship(back_populates="drift_metrics")
