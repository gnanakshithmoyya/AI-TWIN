from __future__ import annotations
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session

from app.auth.database import SessionLocal, engine
from app.auth.security import decode_token
from app.chat_store.models import Base
from app.chat_store import repo
from app.chat import process_chat  # to reuse logic
from app.chat import ChatRequest


Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/chats", tags=["chats"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_user(authorization: str) -> int:
    from app.chat import decode_token_from_header
    return decode_token_from_header(authorization, expected_type="access")


@router.get("")
def list_chats(authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = require_user(authorization)
    chats = repo.list_chats(db, user_id)
    return [
        {"chat_id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat()}
        for c in chats
    ]


@router.post("")
def create_chat(title: Optional[str] = None, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = require_user(authorization)
    chat = repo.create_chat(db, user_id, title)
    return {"chat_id": chat.id, "title": chat.title}


@router.get("/{chat_id}/messages")
def get_messages(chat_id: int, authorization: str = Header(None), db: Session = Depends(get_db), limit: int = Query(50, le=100)):
    user_id = require_user(authorization)
    chat = repo.get_chat(db, chat_id, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    msgs = repo.get_messages(db, chat, limit=limit)
    return [
        {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in msgs
    ]


@router.post("/{chat_id}/messages")
def post_message(chat_id: int, payload: ChatRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = require_user(authorization)
    chat = repo.get_chat(db, chat_id, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    # Determine required consents
    from app.consent.repo import get_consent_map
    from app.consent.utils import scopes_for_health_state
    required_scopes = set()
    required_scopes.update(scopes_for_health_state(payload.health_state))
    required_scopes.add("chat_history")
    required_scopes.add("memory_personalization")
    consent_map = get_consent_map(db, user_id)
    missing = [s for s in required_scopes if not consent_map.get(s, False)]
    if missing:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "consent_required",
                "required_scopes": missing,
                "message": "Please grant consent to continue."
            }
        )
    # re-use chat_with_twin; it requires chat_id in payload? we will pass via wrapper
    # add chat_id to request context by attaching to payload health_state? we pass separately through dependency
    # store user message
    if consent_map.get("chat_history"):
        repo.add_message(db, chat, user_id, role="user", content=payload.question)
    reply = process_chat(
        user_id=user_id,
        payload=payload,
        chat_context={"chat": chat, "db": db, "user_id": user_id, "consent_map": consent_map},
    )
    if consent_map.get("chat_history"):
        repo.add_message(db, chat, user_id, role="twin", content=reply["reply"])
    # auto title if missing
    if not chat.title:
        chat.title = payload.question[:50]
        db.commit()
    return reply
