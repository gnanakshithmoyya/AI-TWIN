from fastapi.testclient import TestClient
import app.chat as chat_module
from app.main import app
import httpx

chat_module.ollama.chat = lambda **kwargs: {"message": {"content": "stubbed reply"}}

client = TestClient(app)


def auth_user(email: str, password: str = "StrongPass123"):
    client.post("/auth/signup", json={"email": email, "password": password})
    r = client.post("/auth/login", json={"email": email, "password": password})
    token = r.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


def test_wearables_consent_required(monkeypatch):
    headers = auth_user("wear1@example.com")
    # revoke all scopes
    for scope in ["wearables_connect", "wearables_sync", "sleep_data", "activity_data", "steps_activity_data", "heart_rate_data", "glucose_data"]:
        client.post("/consent/revoke", headers=headers, json={"scope": scope})

    # connect without consent -> 403
    r = client.post("/wearables/connect", headers=headers, json={"provider": "fitbit"})
    assert r.status_code == 403

    # grant connect
    client.post("/consent/grant", headers=headers, json={"scope": "wearables_connect"})
    monkeypatch.setenv("FITBIT_CLIENT_ID", "cid")
    monkeypatch.setenv("FITBIT_CLIENT_SECRET", "secret")
    monkeypatch.setenv("FITBIT_REDIRECT_URI", "http://localhost/cb")
    monkeypatch.setenv("FITBIT_AUTH_SCOPES", "activity heartrate sleep profile")
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: type("Resp", (), {"raise_for_status": lambda self: None, "json": lambda self: {"access_token": "a", "refresh_token": "r", "expires_in": 3600}})())
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: type("Resp", (), {"raise_for_status": lambda self: None, "json": lambda self: {}})())
    r2 = client.post("/wearables/connect", headers=headers, json={"provider": "fitbit"})
    assert r2.status_code == 200
    # simulate callback to store tokens
    client.post("/wearables/callback", headers=headers, json={"provider": "fitbit", "code": "dummy"})

    # sync without signal scopes -> 403
    r3 = client.post("/wearables/sync", headers=headers, json={"provider": "fitbit"})
    assert r3.status_code == 403

    # grant sync + activity_data + steps_activity_data
    client.post("/consent/grant-bulk", headers=headers, json={"scopes": ["wearables_sync", "activity_data", "steps_activity_data"]})
    r4 = client.post("/wearables/sync", headers=headers, json={"provider": "fitbit", "signals": ["activity_steps"]})
    assert r4.status_code == 200
    body = r4.json()
    assert body.get("health_state") == {}  # stubbed empty


def test_wearables_cross_user_isolation():
    headers1 = auth_user("wear2@example.com")
    headers2 = auth_user("wear3@example.com")
    client.post("/consent/grant-bulk", headers=headers1, json={"scopes": ["wearables_connect", "wearables_sync", "activity_data"]})
    r = client.post("/wearables/sync", headers=headers2, json={"provider": "fitbit", "signals": ["activity_steps"]})
    # user2 has no consent → 403
    assert r.status_code == 403
