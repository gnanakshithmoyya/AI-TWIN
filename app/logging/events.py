from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

LOG_PATH = Path("logs/events.jsonl")


def ensure_log_dir():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_event(event: Dict[str, Any]) -> None:
    """Write a single JSONL event. Avoids raising errors to keep request path fast."""
    try:
        ensure_log_dir()
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=True) + "\n")
    except Exception:
        # Logging must never break the main flow
        return


def make_event(
    intent: str,
    intent_confidence: float,
    question: str,
    health_state: Dict[str, Any],
    missing_fields,
    safety: Dict[str, Any],
    latency_ms: float,
    store_raw_question: bool = False,
) -> Dict[str, Any]:
    fields_present = {k: True for k in health_state.keys()}
    evt = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "request_id": str(uuid.uuid4()),
        "intent": intent,
        "intent_confidence": round(intent_confidence, 2),
        "question_chars": len(question or ""),
        "fields_present": fields_present,
        "missing_fields": missing_fields,
        "safety": safety,
        "latency_ms": round(latency_ms, 2),
    }
    if store_raw_question:
        evt["question"] = question
    return evt
