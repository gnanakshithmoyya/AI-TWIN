from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.auth.database import SessionLocal, engine
from app.auth.models import Base, User
from app.auth.schemas import SignupRequest, LoginRequest, TokenPair, UserPublic
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Ensure tables exist on import
Base.metadata.create_all(bind=engine)


@router.post("/signup", response_model=UserPublic)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.to_public()


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(authorization: str = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing refresh token")
    token = authorization.split(" ", 1)[1]
    user_id = decode_token(token, expected_type="refresh")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return TokenPair(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/logout")
def logout():
    # Stateless JWT: client should discard tokens; server could add blacklist if needed later
    return {"detail": "Logged out. Please discard your tokens."}
