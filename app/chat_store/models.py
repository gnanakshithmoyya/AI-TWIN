from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.auth.models import Base


class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")
    summaries = relationship("ChatSummary", back_populates="chat", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" or "twin"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chat = relationship("Chat", back_populates="messages")


class ChatSummary(Base):
    __tablename__ = "chat_summaries"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    summary = Column(Text, nullable=False)  # short recap, no raw values
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    chat = relationship("Chat", back_populates="summaries")


class UserMemory(Base):
    __tablename__ = "user_memory"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    kind = Column(String, nullable=False)  # e.g., topic_pattern, preference, trend_summary, missing_field_pattern, signal_summary
    content = Column(Text, nullable=False)  # no raw values or diagnoses
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
