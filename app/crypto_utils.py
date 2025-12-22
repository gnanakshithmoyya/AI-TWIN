from __future__ import annotations
from typing import Optional
try:
    from cryptography.fernet import Fernet, InvalidToken  # type: ignore
except ImportError:
    # Fallback minimal stub (NOT secure). For environments without cryptography installed.
    import base64

    class InvalidToken(Exception):
        pass

    class Fernet:  # type: ignore
        def __init__(self, key: bytes):
            self.key = key

        def encrypt(self, data: bytes) -> bytes:
            return base64.urlsafe_b64encode(data)

        def decrypt(self, token: bytes) -> bytes:
            try:
                return base64.urlsafe_b64decode(token)
            except Exception as e:
                raise InvalidToken from e
from app.config import ENCRYPTION_KEY

# ENCRYPTION_KEY should be a 32-byte urlsafe base64 key. In dev, generate with Fernet.generate_key().

def _fernet() -> Optional[Fernet]:
    if not ENCRYPTION_KEY:
        return None
    try:
        return Fernet(ENCRYPTION_KEY)
    except Exception:
        return None


def encrypt_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    f = _fernet()
    if not f:
        return value  # fallback in dev if no key
    return f.encrypt(value.encode()).decode()


def decrypt_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    f = _fernet()
    if not f:
        return value
    try:
        return f.decrypt(value.encode()).decode()
    except InvalidToken:
        # assume plaintext for legacy rows
        return value
