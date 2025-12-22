import os
from typing import Optional


def env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key, default)


JWT_SECRET = env("JWT_SECRET", "change-me-dev-secret")
FITBIT_CLIENT_ID = env("FITBIT_CLIENT_ID", "")
FITBIT_CLIENT_SECRET = env("FITBIT_CLIENT_SECRET", "")
FITBIT_REDIRECT_URI = env("FITBIT_REDIRECT_URI", "")
FITBIT_AUTH_SCOPES = env("FITBIT_AUTH_SCOPES", "activity heartrate sleep profile")
ENCRYPTION_KEY = env("ENCRYPTION_KEY")  # must be 32 urlsafe-base64 bytes for Fernet
