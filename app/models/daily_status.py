from sqlalchemy import Column, Date, DateTime
from app.core.db import Base


class DailyStatus(Base):
    __tablename__ = "daily_status"

    date = Column(Date, primary_key=True)
    completed_at = Column(DateTime, nullable=True)
