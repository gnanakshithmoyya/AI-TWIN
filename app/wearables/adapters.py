from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime
import os
import base64
import httpx
from app.wearables.models import WearableConnection
from sqlalchemy.orm import Session
from datetime import timedelta
from app.crypto_utils import encrypt_str, decrypt_str
from app.config import FITBIT_CLIENT_ID, FITBIT_CLIENT_SECRET, FITBIT_REDIRECT_URI, FITBIT_AUTH_SCOPES


class WearableAdapter:
    provider: str = "base"

    def get_connect_url(self, user_id: int, redirect_uri: str, scopes: List[str]) -> Optional[str]:
        return None

    def exchange_code(self, user_id: int, code: str, redirect_uri: str, db: Session) -> None:
        raise NotImplementedError

    def disconnect(self, user_id: int, db: Session) -> None:
        raise NotImplementedError

    def supported_signals(self) -> List[str]:
        return []

    def fetch_health_state(self, user_id: int, start: datetime, end: datetime, signals: List[str], db: Session) -> Dict:
        return {}


class HealthKitAdapter(WearableAdapter):
    provider = "healthkit"

    def exchange_code(self, user_id: int, code: str, redirect_uri: str, db: Session) -> None:
        # For on-device HealthKit, code exchange is not applicable; data is expected from client-side sync.
        return

    def disconnect(self, user_id: int, db: Session) -> None:
        return

    def supported_signals(self) -> List[str]:
        return ["activity_steps", "activity_minutes", "sleep_duration", "heart_rate", "resting_heart_rate", "hrv", "spo2", "temperature_deviation", "weight", "bmi", "vo2max", "stress_score", "readiness_score", "blood_pressure", "glucose_cgm", "cycle_tracking"]

    def fetch_health_state(self, user_id: int, start: datetime, end: datetime, signals: List[str], db: Session) -> Dict:
        return {}


class HealthConnectAdapter(WearableAdapter):
    provider = "healthconnect"

    def exchange_code(self, user_id: int, code: str, redirect_uri: str, db: Session) -> None:
        return

    def disconnect(self, user_id: int, db: Session) -> None:
        return

    def supported_signals(self) -> List[str]:
        return ["activity_steps", "activity_minutes", "sleep_duration", "heart_rate", "resting_heart_rate", "hrv", "spo2", "temperature_deviation", "weight", "bmi", "vo2max", "stress_score", "readiness_score", "blood_pressure", "glucose_cgm", "cycle_tracking"]

    def fetch_health_state(self, user_id: int, start: datetime, end: datetime, signals: List[str], db: Session) -> Dict:
        return {}


class FitbitAdapter(WearableAdapter):
    provider = "fitbit"

    def get_connect_url(self, user_id: int, redirect_uri: str, scopes: List[str]) -> Optional[str]:
        client_id = os.getenv("FITBIT_CLIENT_ID", "")
        redirect = redirect_uri or os.getenv("FITBIT_REDIRECT_URI", "")
        scope = os.getenv("FITBIT_AUTH_SCOPES", "activity heartrate sleep profile")
        if not client_id or not redirect:
            return None
        return (
            "https://www.fitbit.com/oauth2/authorize"
            f"?response_type=code&client_id={client_id}"
            f"&redirect_uri={redirect}"
            f"&scope={scope.replace(' ', '%20')}"
        )

    def _basic_auth(self) -> str:
        cid = os.getenv("FITBIT_CLIENT_ID", "")
        secret = os.getenv("FITBIT_CLIENT_SECRET", "")
        raw = f"{cid}:{secret}".encode()
        return base64.b64encode(raw).decode()

    def _request_token(self, data: dict) -> dict:
        headers = {
            "Authorization": f"Basic {self._basic_auth()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        resp = httpx.post("https://api.fitbit.com/oauth2/token", data=data, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def exchange_code(self, user_id: int, code: str, redirect_uri: str, db: Session) -> None:
        redirect = redirect_uri or os.getenv("FITBIT_REDIRECT_URI", "")
        token_data = self._request_token(
            {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect}
        )
        self._store_tokens(db, user_id, token_data)

    def disconnect(self, user_id: int, db: Session) -> None:
        db.query(WearableConnection).filter(
            WearableConnection.user_id == user_id, WearableConnection.provider == self.provider
        ).delete()
        db.commit()

    def supported_signals(self) -> List[str]:
        return ["activity_steps", "activity_minutes", "calories_burned", "sleep_duration", "sleep_stages", "heart_rate", "resting_heart_rate", "hrv", "spo2", "weight", "bmi", "vo2max"]

    def _store_tokens(self, db: Session, user_id: int, token_data: dict):
        access_plain = token_data.get("access_token")
        refresh_plain = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in") or 0
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        access = encrypt_str(access_plain)
        refresh = encrypt_str(refresh_plain)
        conn = (
            db.query(WearableConnection)
            .filter(WearableConnection.user_id == user_id, WearableConnection.provider == self.provider)
            .first()
        )
        if not conn:
            conn = WearableConnection(
                user_id=user_id,
                provider=self.provider,
                access_token=access,
                refresh_token=refresh,
                expires_at=expires_at,
            )
            db.add(conn)
        else:
            conn.access_token = access
            conn.refresh_token = refresh
            conn.expires_at = expires_at
        db.commit()

    def _refresh_if_needed(self, db: Session, conn: WearableConnection):
        if not conn.expires_at or conn.expires_at > datetime.utcnow():
            return decrypt_str(conn.access_token)
        refresh_plain = decrypt_str(conn.refresh_token)
        token_data = self._request_token(
            {"grant_type": "refresh_token", "refresh_token": refresh_plain}
        )
        self._store_tokens(db, conn.user_id, token_data)
        return token_data.get("access_token")

    def _api_get(self, access_token: str, url: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = httpx.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def fetch_health_state(self, user_id: int, start: datetime, end: datetime, signals: List[str], db: Session) -> Dict:
        conn = (
            db.query(WearableConnection)
            .filter(WearableConnection.user_id == user_id, WearableConnection.provider == self.provider)
            .first()
        )
        if not conn or not conn.access_token:
            raise httpx.HTTPStatusError("Not connected", request=None, response=None)

        access = self._refresh_if_needed(db, conn)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        health_state: Dict[str, any] = {}

        if "activity_steps" in signals or "activity_minutes" in signals or "calories_burned" in signals:
            data = self._api_get(access, f"https://api.fitbit.com/1/user/-/activities/date/{today}.json")
            summary = data.get("summary", {})
            if summary:
                if "steps" in summary:
                    health_state["activity_steps"] = summary.get("steps")
                active_minutes = (
                    summary.get("veryActiveMinutes", 0)
                    + summary.get("fairlyActiveMinutes", 0)
                    + summary.get("lightlyActiveMinutes", 0)
                )
                if active_minutes:
                    health_state["activity_minutes"] = active_minutes
                if "caloriesOut" in summary:
                    health_state["calories_burned"] = summary.get("caloriesOut")

        if "heart_rate" in signals or "resting_heart_rate" in signals:
            data = self._api_get(access, f"https://api.fitbit.com/1/user/-/activities/heart/date/{today}/1d.json")
            activities = data.get("activities-heart", [])
            if activities:
                first = activities[0].get("value", {})
                if "restingHeartRate" in first:
                    health_state["resting_heart_rate"] = first.get("restingHeartRate")
                zones = first.get("heartRateZones", [])
                if zones:
                    # approximate average from zones midpoints weighted by minutes
                    total_minutes = sum(z.get("minutes", 0) for z in zones)
                    if total_minutes > 0:
                        avg = 0.0
                        for z in zones:
                            mid = (z.get("min", 0) + z.get("max", z.get("min", 0))) / 2
                            avg += mid * z.get("minutes", 0)
                        health_state["heart_rate_avg"] = round(avg / total_minutes, 1)

        if "sleep_duration" in signals or "sleep_stages" in signals or "sleep" in signals:
            data = self._api_get(access, f"https://api.fitbit.com/1.2/user/-/sleep/date/{today}.json")
            sleeps = data.get("sleep", [])
            if sleeps:
                main = sleeps[0]
                minutes = main.get("minutesAsleep", 0)
                health_state["sleep_hours"] = round(minutes / 60, 2)
                stages = main.get("levels", {}).get("summary", {})
                if stages:
                    health_state["sleep_stages"] = {
                        "light": stages.get("light", {}).get("minutes"),
                        "deep": stages.get("deep", {}).get("minutes"),
                        "rem": stages.get("rem", {}).get("minutes"),
                        "awake": stages.get("wake", {}).get("minutes"),
                    }

        return health_state


class WhoopAdapter(WearableAdapter):
    provider = "whoop"

    def exchange_code(self, user_id: int, code: str, redirect_uri: str) -> None:
        return

    def disconnect(self, user_id: int) -> None:
        return

    def supported_signals(self) -> List[str]:
        return ["sleep_duration", "hrv", "resting_heart_rate", "spo2", "stress_score", "readiness_score"]

    def fetch_health_state(self, user_id: int, start: datetime, end: datetime, signals: List[str]) -> Dict:
        return {}


ADAPTERS = {
    "healthkit": HealthKitAdapter(),
    "healthconnect": HealthConnectAdapter(),
    "fitbit": FitbitAdapter(),
    "whoop": WhoopAdapter(),
}
