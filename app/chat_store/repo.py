from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.chat_store.models import Chat, ChatMessage, ChatSummary, UserMemory
from datetime import datetime


def create_chat(db: Session, user_id: int, title: Optional[str]) -> Chat:
    chat = Chat(user_id=user_id, title=title or None)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def list_chats(db: Session, user_id: int) -> List[Chat]:
    return db.query(Chat).filter(Chat.user_id == user_id).order_by(desc(Chat.updated_at)).all()


def get_chat(db: Session, chat_id: int, user_id: int) -> Optional[Chat]:
    return db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()


def add_message(db: Session, chat: Chat, user_id: int, role: str, content: str) -> ChatMessage:
    msg = ChatMessage(chat_id=chat.id, user_id=user_id, role=role, content=content)
    chat.updated_at = datetime.utcnow()
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_messages(db: Session, chat: Chat, limit: int = 50) -> List[ChatMessage]:
    return db.query(ChatMessage).filter(ChatMessage.chat_id == chat.id).order_by(desc(ChatMessage.created_at)).limit(limit).all()


def upsert_chat_summary(db: Session, chat: Chat, summary_text: str):
    # keep only latest 5 summaries per chat to bound storage
    summary = ChatSummary(chat_id=chat.id, summary=summary_text)
    db.add(summary)
    db.commit()
    # prune older summaries
    old = (
        db.query(ChatSummary)
        .filter(ChatSummary.chat_id == chat.id)
        .order_by(desc(ChatSummary.created_at))
        .all()
    )
    if len(old) > 5:
        for s in old[5:]:
            db.delete(s)
        db.commit()


def add_user_memory(db: Session, user_id: int, kind: str, content: str):
    entry = UserMemory(user_id=user_id, kind=kind, content=content)
    db.add(entry)
    db.commit()

    # bound memory to last 20 per kind
    old = (
        db.query(UserMemory)
        .filter(UserMemory.user_id == user_id, UserMemory.kind == kind)
        .order_by(desc(UserMemory.created_at))
        .all()
    )
    if len(old) > 20:
        for e in old[20:]:
            db.delete(e)
        db.commit()


def retrieve_chat_summaries(db: Session, chat_id: int, limit: int = 2) -> List[str]:
    rows = (
        db.query(ChatSummary)
        .filter(ChatSummary.chat_id == chat_id)
        .order_by(desc(ChatSummary.created_at))
        .limit(limit)
        .all()
    )
    return [r.summary for r in rows]


def retrieve_user_memory(db: Session, user_id: int, limit: int = 3, keywords: Optional[List[str]] = None) -> List[str]:
    q = db.query(UserMemory).filter(UserMemory.user_id == user_id).order_by(desc(UserMemory.updated_at))
    rows = q.limit(limit).all()
    # simple keyword filter to prefer matches
    if keywords:
        matched = []
        unmatched = []
        lowered = [k.lower() for k in keywords]
        for r in rows:
            if any(k in r.content.lower() for k in lowered):
                matched.append(r)
            else:
                unmatched.append(r)
        rows = matched + unmatched
    return [r.content for r in rows[:limit]]
