from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json

from app.auth.database import SessionLocal, engine
from app.auth.security import decode_token
from app.wearables.models import Base, WearableConnection, WearableSyncLog
from app.wearables.snapshots import UserHealthStateSnapshot
from app.wearables.adapters import ADAPTERS, FitbitAdapter
from app.consent.repo import get_consent_map
from app.consent.utils import ALL_SCOPES
from app.consent.utils import scopes_for_health_state

Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/wearables", tags=["wearables"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_user(authorization: str) -> int:
    from app.chat import decode_token_from_header
    return decode_token_from_header(authorization, expected_type="access")


class ConnectRequest(BaseModel):
    provider: str
    redirect_uri: Optional[str] = None


class CallbackRequest(BaseModel):
    provider: str
    code: str
    redirect_uri: Optional[str] = None


class DisconnectRequest(BaseModel):
    provider: str


class SyncRequest(BaseModel):
    provider: str
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    signals: Optional[List[str]] = None


class IngestRequest(BaseModel):
    provider: str
    health_state: dict
    timestamp: Optional[datetime] = None


def _require_scope(consent_map, scopes: List[str]):
    missing = [s for s in scopes if not consent_map.get(s, False)]
    if missing:
        raise HTTPException(
            status_code=403,
            detail={"error": "consent_required", "required_scopes": missing, "message": "Please grant consent to continue."},
        )


def _signal_scopes(signals: List[str]) -> List[str]:
    required = set()
    for s in signals:
        if s.startswith("activity_steps") or s == "steps":
            required.add("steps_activity_data")
        if s.startswith("activity_"):
            required.add("activity_data")
        elif s in ["heart_rate", "resting_heart_rate", "heart_rate_avg"]:
            required.add("heart_rate_data")
        elif s == "hrv":
            required.add("hrv_data")
        elif s.startswith("sleep_"):
            required.add("sleep_data")
        elif s == "spo2":
            required.add("spo2_data")
        elif s == "temperature_deviation":
            required.add("temperature_data")
        elif s in ["weight", "bmi"]:
            required.add("body_data")
        elif s == "vo2max":
            required.add("vo2max_data")
        elif s == "stress_score":
            required.add("stress_data")
        elif s == "readiness_score":
            required.add("readiness_data")
        elif s == "blood_pressure":
            required.add("blood_pressure_data")
        elif s == "glucose_cgm":
            required.add("glucose_cgm_data")
        elif s == "cycle_tracking":
            required.add("cycle_tracking_data")
    return list(required)


@router.get("/status")
def status(authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = require_user(authorization)
    rows = db.query(WearableConnection).filter(WearableConnection.user_id == user_id).all()
    logs = db.query(WearableSyncLog).filter(WearableSyncLog.user_id == user_id).all()
    sync_map = {(l.provider): l.last_sync_at for l in logs}
    return [{"provider": r.provider, "connected_at": r.created_at, "last_sync_at": sync_map.get(r.provider)} for r in rows]


@router.post("/connect")
def connect(payload: ConnectRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = require_user(authorization)
    consent = get_consent_map(db, user_id)
    _require_scope(consent, ["wearables_connect"])
    adapter = ADAPTERS.get(payload.provider)
    if not adapter:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    url = adapter.get_connect_url(user_id, payload.redirect_uri or "", [])
    return {"connect_url": url, "provider": payload.provider}


@router.post("/callback")
def callback(payload: CallbackRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = require_user(authorization)
    consent = get_consent_map(db, user_id)
    _require_scope(consent, ["wearables_connect"])
    adapter = ADAPTERS.get(payload.provider)
    if not adapter:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    adapter.exchange_code(user_id, payload.code, payload.redirect_uri or "", db)
    return {"provider": payload.provider, "status": "connected"}


@router.post("/disconnect")
def disconnect(payload: DisconnectRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = require_user(authorization)
    adapter = ADAPTERS.get(payload.provider)
    if not adapter:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    adapter.disconnect(user_id, db)
    db.query(WearableConnection).filter(WearableConnection.user_id == user_id, WearableConnection.provider == payload.provider).delete()
    db.commit()
    return {"provider": payload.provider, "status": "disconnected"}


@router.post("/sync")
def sync(payload: SyncRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    user_id = require_user(authorization)
    consent = get_consent_map(db, user_id)
    _require_scope(consent, ["wearables_sync"])
    adapter = ADAPTERS.get(payload.provider)
    if not adapter:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    signals = payload.signals or adapter.supported_signals()
    required = _signal_scopes(signals)
    _require_scope(consent, required)

    data = adapter.fetch_health_state(user_id, payload.start or datetime.utcnow(), payload.end or datetime.utcnow(), signals, db)

    # log sync
    log = db.query(WearableSyncLog).filter(WearableSyncLog.user_id == user_id, WearableSyncLog.provider == payload.provider).first()
    if not log:
        log = WearableSyncLog(user_id=user_id, provider=payload.provider, last_sync_at=datetime.utcnow(), status="ok")
        db.add(log)
    else:
        log.last_sync_at = datetime.utcnow()
        log.status = "ok"
    db.commit()

    # normalize: ensure ts/value/source for each entry
    normalized = data or {}
    return {"provider": payload.provider, "last_synced_at": datetime.utcnow().isoformat(), "health_state": normalized}


@router.post("/ingest")
def ingest(payload: IngestRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    """
    For iOS clients to push normalized HealthKit data.
    """
    user_id = require_user(authorization)
    if payload.provider != "healthkit":
        raise HTTPException(status_code=400, detail="Unsupported provider")
    consent = get_consent_map(db, user_id)
    _require_scope(consent, ["wearables_sync"])
    signals = list(payload.health_state.keys())
    required = _signal_scopes(signals)
    _require_scope(consent, required)

    snapshot = UserHealthStateSnapshot(
        user_id=user_id,
        provider=payload.provider,
        payload_json=json.dumps(payload.health_state),
    )
    db.add(snapshot)
    db.commit()
    return {"status": "stored", "provider": payload.provider}
