import json
from pathlib import Path
from app.logging.events import make_event, log_event, LOG_PATH


def test_log_event_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setattr("app.logging.events.LOG_PATH", tmp_path / "events.jsonl")
    evt = make_event(
        intent="SLEEP_RECAP",
        intent_confidence=0.9,
        question="How did I sleep?",
        health_state={"sleep_hours": 7},
        missing_fields=[],
        safety={"medication_refusal": False, "diagnosis_refusal": False},
        latency_ms=123.4,
        store_raw_question=False,
    )
    log_event(evt)
    content = (tmp_path / "events.jsonl").read_text().strip()
    assert content, "Log file should not be empty"
    payload = json.loads(content)
    assert "question" not in payload  # no raw question stored by default
    assert payload["question_chars"] == len("How did I sleep?")
