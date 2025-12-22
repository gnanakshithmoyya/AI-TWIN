from fastapi.testclient import TestClient
import app.chat as chat_module
from app.main import app
from app.auth.database import SessionLocal
from app.wearables.snapshots import UserHealthStateSnapshot
import json

chat_module.ollama.chat = lambda **kwargs: {"message": {"content": "stubbed reply"}}

client = TestClient(app)


def auth_user(email: str, password: str = "StrongPass123"):
    client.post("/auth/signup", json={"email": email, "password": password})
    r = client.post("/auth/login", json={"email": email, "password": password})
    token = r.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


def test_healthkit_ingest_consent():
    headers = auth_user("hk1@example.com")
    # revoke to start clean
    for scope in ["wearables_sync", "sleep_data", "heart_rate_data", "steps_activity_data"]:
        client.post("/consent/revoke", headers=headers, json={"scope": scope})

    payload = {
        "provider": "healthkit",
        "health_state": {"steps": 8200, "sleep_hours": 6.8, "resting_heart_rate": 58},
        "timestamp": "2025-12-22T00:00:00Z"
    }
    r = client.post("/wearables/ingest", headers=headers, json=payload)
    assert r.status_code == 403
    # Grant needed scopes
    client.post("/consent/grant-bulk", headers=headers, json={"scopes": ["wearables_sync", "sleep_data", "heart_rate_data", "steps_activity_data"]})
    r2 = client.post("/wearables/ingest", headers=headers, json=payload)
    assert r2.status_code == 200
    assert r2.json().get("status") == "stored"

    # verify snapshot stored
    db = SessionLocal()
    rows = db.query(UserHealthStateSnapshot).all()
    assert rows, "Expected at least one snapshot"
    db.close()
