from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from app.core.db import Base


class FitbitMetric(Base):
    __tablename__ = "fitbit_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    metric_type = Column(String, nullable=False, index=True)  # 'steps', 'sleep_minutes', etc.
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)  # 'steps', 'minutes', 'score', etc.
    extra_data = Column(JSON, nullable=True)  # Additional metric details
    synced_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        # Composite unique index: one metric type per user per date
        Index('ix_fitbit_metrics_user_date_type', 'user_id', 'date', 'metric_type', unique=True),
        Index('ix_fitbit_metrics_user_date', 'user_id', 'date'),
    )
