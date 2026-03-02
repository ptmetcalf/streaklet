from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.core.db import Base


class CustomList(Base):
    __tablename__ = "custom_lists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    icon = Column(String, nullable=True)
    template_key = Column(String, nullable=True)
    is_enabled = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_custom_lists_user_name"),
        UniqueConstraint("user_id", "template_key", name="uq_custom_lists_user_template_key"),
    )
