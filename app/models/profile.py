from sqlalchemy import Column, Integer, String, DateTime, Boolean, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    color = Column(String, default="#3b82f6", nullable=False)
    confetti_enabled = Column(Boolean, nullable=False, default=True, server_default=text("1"))
    show_shopping_list = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    fitbit_preferences = relationship("FitbitPreferences", back_populates="profile", uselist=False, cascade="all, delete-orphan")
