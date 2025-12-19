from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.security import decode_token
from app.auth.database import SessionLocal, engine
from app.consent.models import Base, UserConsent
from app.consent.repo import get_consent_map, grant_scope, revoke_scope, grant_bulk
from app.consent.utils import ALL_SCOPES

Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/consent", tags=["consent"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_user(authorization: str) -> int:
    from app.chat import decode_token_from_header
    return decode_token_from_header(authorization, expected_type="access")


class ScopeRequest(BaseModel):
    scope: str


class BulkScopeRequest(BaseModel):
    scopes: List[str]


@router.get("")
def list_consent(authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = require_user(authorization)
    return get_consent_map(db, user_id)


@router.post("/grant")
def grant(payload: ScopeRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = require_user(authorization)
    if payload.scope not in ALL_SCOPES:
        raise HTTPException(status_code=400, detail="Unknown scope")
    grant_scope(db, user_id, payload.scope, source="api")
    return get_consent_map(db, user_id)


@router.post("/revoke")
def revoke(payload: ScopeRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = require_user(authorization)
    if payload.scope not in ALL_SCOPES:
        raise HTTPException(status_code=400, detail="Unknown scope")
    revoke_scope(db, user_id, payload.scope)
    return get_consent_map(db, user_id)


@router.post("/grant-bulk")
def grant_bulk_endpoint(payload: BulkScopeRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = require_user(authorization)
    for s in payload.scopes:
        if s not in ALL_SCOPES:
            raise HTTPException(status_code=400, detail=f"Unknown scope: {s}")
    grant_bulk(db, user_id, payload.scopes, source="api")
    return get_consent_map(db, user_id)
