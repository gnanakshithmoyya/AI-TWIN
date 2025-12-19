from __future__ import annotations
from datetime import datetime
from typing import Dict, List
from sqlalchemy.orm import Session
from app.consent.models import UserConsent
from app.consent.utils import ALL_SCOPES


def get_consent_map(db: Session, user_id: int) -> Dict[str, bool]:
    grants = {scope: False for scope in ALL_SCOPES}
    rows = db.query(UserConsent).filter(UserConsent.user_id == user_id).all()
    for r in rows:
        grants[r.scope] = bool(r.granted)
    return grants


def grant_scope(db: Session, user_id: int, scope: str, source: str = "api"):
    now = datetime.utcnow()
    uc = db.query(UserConsent).filter(UserConsent.user_id == user_id, UserConsent.scope == scope).first()
    if uc:
        uc.granted = True
        uc.granted_at = now
        uc.revoked_at = None
        uc.source = source
    else:
        uc = UserConsent(user_id=user_id, scope=scope, granted=True, granted_at=now, revoked_at=None, source=source)
        db.add(uc)
    db.commit()


def revoke_scope(db: Session, user_id: int, scope: str):
    now = datetime.utcnow()
    uc = db.query(UserConsent).filter(UserConsent.user_id == user_id, UserConsent.scope == scope).first()
    if uc:
        uc.granted = False
        uc.revoked_at = now
        db.commit()
    else:
        uc = UserConsent(user_id=user_id, scope=scope, granted=False, granted_at=None, revoked_at=now, source="api")
        db.add(uc)
        db.commit()


def grant_bulk(db: Session, user_id: int, scopes: List[str], source: str = "api"):
    for s in scopes:
        grant_scope(db, user_id, s, source=source)
