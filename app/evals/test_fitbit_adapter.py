import os
from datetime import datetime
from app.wearables.adapters import FitbitAdapter
from app.wearables.models import WearableConnection
from app.auth.database import SessionLocal


def test_fitbit_connect_url_env(monkeypatch):
    monkeypatch.setenv("FITBIT_CLIENT_ID", "cid")
    monkeypatch.setenv("FITBIT_CLIENT_SECRET", "secret")
    monkeypatch.setenv("FITBIT_REDIRECT_URI", "http://localhost/callback")
    adapter = FitbitAdapter()
    url = adapter.get_connect_url(1, "", [])
    assert "client_id=cid" in url
    assert "redirect_uri=http://localhost/callback" in url


def test_fitbit_fetch_mapping(monkeypatch):
    # Mock requests
    calls = {}

    def fake_get(url, headers=None, timeout=10):
        class Resp:
            def raise_for_status(self): ...
            def json(self):
                if "activities/date" in url:
                    return {"summary": {"steps": 1234, "veryActiveMinutes": 10, "fairlyActiveMinutes": 5, "lightlyActiveMinutes": 15, "caloriesOut": 2000}}
                if "activities/heart/date" in url:
                    return {"activities-heart": [{"value": {"restingHeartRate": 60, "heartRateZones": [{"min": 30, "max": 100, "minutes": 60}, {"min": 100, "max": 140, "minutes": 30}]}}]}
                if "sleep/date" in url:
                    return {"sleep": [{"minutesAsleep": 420, "levels": {"summary": {"light": {"minutes": 200}, "deep": {"minutes": 80}, "rem": {"minutes": 120}, "wake": {"minutes": 40}}}}]}
                return {}
        calls[url] = True
        return Resp()

    monkeypatch.setenv("FITBIT_CLIENT_ID", "cid")
    monkeypatch.setenv("FITBIT_CLIENT_SECRET", "secret")
    monkeypatch.setenv("FITBIT_REDIRECT_URI", "http://localhost/callback")
    monkeypatch.setenv("FITBIT_AUTH_SCOPES", "activity heartrate sleep profile")

    import httpx
    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: type("Resp", (), {"raise_for_status": lambda self: None, "json": lambda self: {"access_token": "a", "refresh_token": "r", "expires_in": 3600}})())

    adapter = FitbitAdapter()
    db = SessionLocal()
    # ensure clean slate for this user/provider
    db.query(WearableConnection).filter(
        WearableConnection.user_id == 9999,
        WearableConnection.provider == "fitbit",
    ).delete()
    db.commit()
    # seed connection
    conn = WearableConnection(user_id=9999, provider="fitbit", access_token="a", refresh_token="r")
    db.add(conn)
    db.commit()

    hs = adapter.fetch_health_state(9999, datetime.utcnow(), datetime.utcnow(), ["activity_steps", "heart_rate", "sleep_duration"], db)
    assert hs["activity_steps"] == 1234
    assert hs["activity_minutes"] == 30
    assert hs["calories_burned"] == 2000
    assert hs["resting_heart_rate"] == 60
    assert "heart_rate_avg" in hs
    assert hs["sleep_hours"] == 7.0
    assert hs["sleep_stages"]["light"] == 200
    db.query(WearableConnection).filter(WearableConnection.user_id == 9999).delete()
    db.commit()
    db.close()
