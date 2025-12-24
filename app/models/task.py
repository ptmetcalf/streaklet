from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.db import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_required = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Fitbit integration fields
    fitbit_metric_type = Column(String, nullable=True, index=True)
    fitbit_goal_value = Column(Float, nullable=True)
    fitbit_goal_operator = Column(String, nullable=True)  # 'gte', 'lte', 'eq'
    fitbit_auto_check = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
