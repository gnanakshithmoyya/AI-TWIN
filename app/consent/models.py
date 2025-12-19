from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint
from app.auth.models import Base


class UserConsent(Base):
    __tablename__ = "user_consent"
    __table_args__ = (UniqueConstraint("user_id", "scope", name="uq_user_scope"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    scope = Column(String, nullable=False, index=True)
    granted = Column(Boolean, default=False, nullable=False)
    granted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    source = Column(String, nullable=False, default="api")  # ui | api
