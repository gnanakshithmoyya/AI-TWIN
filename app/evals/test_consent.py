from fastapi.testclient import TestClient
import app.chat as chat_module
from app.main import app


# stub LLM
chat_module.ollama.chat = lambda **kwargs: {"message": {"content": "stubbed reply"}}

client = TestClient(app)


def auth_user(email: str, password: str = "StrongPass123"):
    client.post("/auth/signup", json={"email": email, "password": password})
    r = client.post("/auth/login", json={"email": email, "password": password})
    token = r.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


def test_consent_required_and_grant_flow():
    headers = auth_user("consent1@example.com")
    # ensure clean slate: revoke all scopes if any persisted
    for scope in ["profile_basic", "chat_history", "memory_personalization", "sleep_data", "activity_data", "heart_rate_data", "glucose_data", "future_wearables"]:
        client.post("/consent/revoke", headers=headers, json={"scope": scope})
    # create chat
    chat_id = client.post("/chats", headers=headers).json()["chat_id"]
    # without consent -> 403
    r = client.post(
        f"/chats/{chat_id}/messages",
        headers=headers,
        json={"question": "Glucose?", "health_state": {"fasting_glucose": 118}},
    )
    assert r.status_code == 403
    detail = r.json().get("detail", {})
    assert "glucose_data" in detail.get("required_scopes", [])
    assert "chat_history" in detail.get("required_scopes", [])
    assert "memory_personalization" in detail.get("required_scopes", [])

    # grant needed scopes
    client.post(
        "/consent/grant-bulk",
        headers=headers,
        json={"scopes": ["chat_history", "memory_personalization", "glucose_data"]},
    )
    r2 = client.post(
        f"/chats/{chat_id}/messages",
        headers=headers,
        json={"question": "Glucose?", "health_state": {"fasting_glucose": 118}},
    )
    assert r2.status_code == 200
    assert "reply" in r2.json()

    # revoke memory -> should block
    client.post("/consent/revoke", headers=headers, json={"scope": "memory_personalization"})
    r3 = client.post(
        f"/chats/{chat_id}/messages",
        headers=headers,
        json={"question": "Again?", "health_state": {"fasting_glucose": 118}},
    )
    assert r3.status_code == 403
    assert "memory_personalization" in r3.json().get("detail", {}).get("required_scopes", [])


def test_cross_user_consent_isolated():
    headers1 = auth_user("consent2@example.com")
    chat_id = client.post("/chats", headers=headers1).json()["chat_id"]
    # user1 grants
    client.post(
        "/consent/grant-bulk",
        headers=headers1,
        json={"scopes": ["chat_history", "memory_personalization", "glucose_data"]},
    )
    headers2 = auth_user("consent3@example.com")
    # user2 cannot use chat without own consent
    r = client.post(
        f"/chats/{chat_id}/messages",
        headers=headers2,
        json={"question": "Try?", "health_state": {"fasting_glucose": 118}},
    )
    assert r.status_code in (404, 403)
