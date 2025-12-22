from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.auth.models import Base


class UserHealthStateSnapshot(Base):
    __tablename__ = "user_health_state_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)
    payload_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
