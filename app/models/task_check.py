from sqlalchemy import Column, Date, Integer, Boolean, DateTime, ForeignKey, PrimaryKeyConstraint
from app.core.db import Base


class TaskCheck(Base):
    __tablename__ = "task_checks"

    date = Column(Date, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    checked = Column(Boolean, nullable=False, default=False)
    checked_at = Column(DateTime, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'task_id'),
    )
