from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.db import Base


class FitbitConnection(Base):
    __tablename__ = "fitbit_connections"

    user_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True, index=True)
    fitbit_user_id = Column(String, unique=True, nullable=False, index=True)
    access_token = Column(String, nullable=False)  # Stored encrypted
    refresh_token = Column(String, nullable=False)  # Stored encrypted
    token_expires_at = Column(DateTime, nullable=False)
    scope = Column(String, nullable=False)
    connected_at = Column(DateTime, nullable=False, server_default=func.now())
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String, nullable=True)  # 'success', 'error', 'partial'
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
