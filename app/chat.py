# app/chat.py

from __future__ import annotations
from typing import Any, Dict
import time

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
import ollama

from app.rules import evaluate_health
from app.rag.retriever import retrieve
from app.safety import (
    is_forbidden_question,
    check_missing_data,
    response_mentions_unknown_terms,
    DISCLAIMER_TEXT,
)
from app.intent.classifier import classify_intent
from app.prompt.adapter import build_prompt, _clarifying_question
from app.logging.events import log_event, make_event
from app.auth.security import decode_token
from app.chat_store import repo
from app.auth.database import SessionLocal


def decode_token_from_header(header: str, expected_type: str) -> int:
    if not header or not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = header.split(" ", 1)[1]
    user_id = decode_token(token, expected_type=expected_type)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    health_state: Dict[str, Any]  # raw inputs


class SummaryRequest(BaseModel):
    labs: dict = {}
    activity: dict = {}
    sleep: dict = {}
    periods: dict = {}
    other: dict = {}
    # Allow flat fields like fasting_glucose at the top level for convenience
    model_config = {"extra": "allow"}


def require_auth(authorization: str = Header(None)) -> int:
    # Authorization must be checked before body parsing in wrappers
    return decode_token_from_header(authorization, expected_type="access")


def process_chat(user_id: int, payload: ChatRequest, chat_context: Dict[str, Any] = None):
    start = time.monotonic()
    question = (payload.question or "").strip()

    # DB session for chat storage if passed via chat_context
    db = None
    chat = None
    consent_map = None
    if chat_context:
        db = chat_context.get("db")
        chat = chat_context.get("chat")
        consent_map = chat_context.get("consent_map")

    # Consent gating: default deny
    if db:
        from app.consent.repo import get_consent_map
        from app.consent.utils import scopes_for_health_state
        if consent_map is None:
            consent_map = get_consent_map(db, user_id)
        required_scopes = set()
        required_scopes.update(scopes_for_health_state(payload.health_state))
        if chat:
            required_scopes.add("chat_history")
            required_scopes.add("memory_personalization")
        missing = [s for s in required_scopes if not consent_map.get(s, False)]
        if missing:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "consent_required",
                    "required_scopes": missing,
                    "message": "Please grant consent to continue.",
                },
            )

    chat_history_ok = bool(consent_map.get("chat_history")) if consent_map else False
    memory_ok = bool(consent_map.get("memory_personalization")) if consent_map else False
    # 1) Deterministic facts are the source of truth
    facts = evaluate_health(payload.health_state)

    # 2) Hard block: forbidden medical advice topics
    if is_forbidden_question(question):
        latency_ms = (time.monotonic() - start) * 1000
        log_event(
            make_event(
                intent="FORBIDDEN",
                intent_confidence=1.0,
                question=question,
                health_state=payload.health_state,
                missing_fields=[],
                safety={"medication_refusal": True, "diagnosis_refusal": True},
                latency_ms=latency_ms,
            )
        )
        return {
            "reply": (
                "I can’t help with diagnosis or medication decisions. "
                "Please consult a qualified healthcare professional."
            )
        }

    # 3) Classify intent (deterministic)
    intent_result = classify_intent(question, payload.health_state)

    # 4) If user asks about an area but facts don’t contain that signal → refuse
    missing, msg = check_missing_data(question, facts)
    if missing:
        latency_ms = (time.monotonic() - start) * 1000
        log_event(
            make_event(
                intent=intent_result.intent,
                intent_confidence=intent_result.confidence,
                question=question,
                health_state=payload.health_state,
                missing_fields=intent_result.missing_fields or [],
                safety={"medication_refusal": False, "diagnosis_refusal": False},
                latency_ms=latency_ms,
            )
        )
        return {"reply": msg}

    # 5) Retrieve references (for explanation only; cannot override facts)
    refs = retrieve(question + " " + str(facts), top_k=2)

    # 5b) Retrieve chat summaries and user memory
    chat_summaries = []
    user_memory_snippets = []
    if db and chat:
        if chat_history_ok:
            chat_summaries = repo.retrieve_chat_summaries(db, chat.id, limit=2)
        if memory_ok:
            user_memory_snippets = repo.retrieve_user_memory(db, user_id, limit=3, keywords=intent_result.matched_keywords)

    clarifier = _clarifying_question(intent_result)

    # 6) Build prompts via adapter
    system_prompt, user_prompt = build_prompt(
        question=question,
        facts=facts,
        intent_result=intent_result,
        retrieved_docs=refs,
        chat_summaries=chat_summaries,
        user_memory_snippets=user_memory_snippets,
        clarifier=clarifier,
    )

    # 7) Deterministic generation settings
    resp = ollama.chat(
        model="llama3",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "temperature": 0.0,
            "top_p": 0.1,
            "num_predict": 220,
        },
    )

    text = (resp.get("message", {}) or {}).get("content", "").strip()
    if not text:
        text = f"I don’t have enough information to answer that safely.\n\n{DISCLAIMER_TEXT}"

    # 8) Post-check for off-limits terms; fall back if needed
    if response_mentions_unknown_terms(text, facts):
        text = f"I don’t have enough information to answer that safely.\n\n{DISCLAIMER_TEXT}"

    latency_ms = (time.monotonic() - start) * 1000
    log_event(
        make_event(
            intent=intent_result.intent,
            intent_confidence=intent_result.confidence,
            question=question,
            health_state=payload.health_state,
            missing_fields=intent_result.missing_fields or [],
            safety={"medication_refusal": intent_result.intent == "SAFETY_MEDICATION", "diagnosis_refusal": intent_result.intent == "DIAGNOSIS_REQUEST"},
            latency_ms=latency_ms,
        )
    )

    # 9) Persist chat message + summary + memory (without raw values)
    if db and chat:
        try:
            if chat_history_ok:
                repo.upsert_chat_summary(db, chat, summary_text=_make_safe_chat_summary(facts, intent_result))
            if memory_ok:
                repo.add_user_memory(
                    db,
                    user_id=user_id,
                    kind="missing_field_pattern" if intent_result.missing_fields else "topic_pattern",
                    content=_make_user_memory_entry(intent_result, facts),
                )
        except Exception:
            # persistence errors shouldn't break chat
            pass

    return {"reply": text}


@router.post("/twin/chat")
async def chat_with_twin(request: Request, user_id: int = Depends(require_auth), chat_context: Dict[str, Any] = None):
    # Auth checked before body parsing; now parse body
    db = SessionLocal()
    body = await request.json()
    try:
        payload = ChatRequest.model_validate(body)
        ctx = chat_context or {}
        ctx["db"] = ctx.get("db") or db
        return process_chat(user_id, payload, ctx)
    finally:
        db.close()


def _make_safe_chat_summary(facts: Dict[str, Any], intent_result):
    parts = []
    for sig in facts.get("signals", []):
        parts.append(f"{sig.get('name')} ({sig.get('status')})")
    if intent_result and intent_result.intent:
        parts.append(f"intent:{intent_result.intent}")
    return "; ".join(parts)[:240] or "Brief chat summary"


def _make_user_memory_entry(intent_result, facts: Dict[str, Any]) -> str:
    if intent_result.missing_fields:
        return f"Asked about {intent_result.intent}; missing {intent_result.missing_fields[:1]}"
    if intent_result.intent:
        return f"Asked {intent_result.intent}; topics: {', '.join(intent_result.matched_keywords)}"
    return "General question"


@router.post("/twin/summary")
def twin_summary(payload: SummaryRequest, authorization: str = Header(None)):
    # optional auth; if provided, validate to tie to user identity for future history
    if authorization:
        decode_token_from_header(authorization, expected_type="access")
    combined = {}
    for section in (payload.labs, payload.activity, payload.sleep, payload.periods, payload.other):
        if section:
            combined.update(section)
    # Support flat fields passed directly in the request body
    extra_fields = getattr(payload, "__pydantic_extra__", None)
    if extra_fields:
        combined.update(extra_fields)
    return {
        "summary": evaluate_health(combined),
        "disclaimer": DISCLAIMER_TEXT,
    }
