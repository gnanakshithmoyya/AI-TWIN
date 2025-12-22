from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.config import JWT_SECRET

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = JWT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 14


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: int) -> str:
    return create_token({"sub": str(user_id), "type": "access"}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(user_id: int) -> str:
    return create_token({"sub": str(user_id), "type": "refresh"}, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str, expected_type: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return int(payload.get("sub"))
    except (JWTError, ValueError):
        return None
