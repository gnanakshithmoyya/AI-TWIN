from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint
from app.auth.models import Base


class WearableConnection(Base):
    __tablename__ = "wearable_connections"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_provider"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)
    access_token = Column(Text, nullable=True)  # placeholder; secure storage/encryption to be added
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class WearableSyncLog(Base):
    __tablename__ = "wearable_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)
    last_sync_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
