from sqlalchemy import Column, Date, DateTime, Integer, ForeignKey, PrimaryKeyConstraint
from app.core.db import Base


class DailyStatus(Base):
    __tablename__ = "daily_status"

    date = Column(Date, nullable=False)
    user_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('date', 'user_id'),
    )
