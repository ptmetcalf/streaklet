from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Date, ForeignKey, JSON
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

    # Task type discriminator
    task_type = Column(String, nullable=False, default='daily', index=True)

    # Active since date - only counts toward completion on dates >= this
    # Nullable for SQLite compatibility (migration 006 adds as nullable)
    # Application code should set to created_at date if NULL
    active_since = Column(Date, nullable=True, index=True)

    # Punch list fields
    due_date = Column(Date, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)

    # Scheduled task fields
    recurrence_pattern = Column(JSON, nullable=True)
    last_occurrence_date = Column(Date, nullable=True)
    next_occurrence_date = Column(Date, nullable=True, index=True)

    # Fitbit integration fields
    fitbit_metric_type = Column(String, nullable=True, index=True)
    fitbit_goal_value = Column(Float, nullable=True)
    fitbit_goal_operator = Column(String, nullable=True)  # 'gte', 'lte', 'eq'
    fitbit_auto_check = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
