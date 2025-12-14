# app/chat.py

from __future__ import annotations
from typing import Any, Dict
import time

from fastapi import APIRouter
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
from app.prompt.adapter import build_prompt
from app.logging.events import log_event, make_event

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


@router.post("/twin/chat")
def chat_with_twin(payload: ChatRequest):
    start = time.monotonic()
    question = (payload.question or "").strip()

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

    # 6) Build prompts via adapter
    system_prompt, user_prompt = build_prompt(question, facts, intent_result, refs)

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

    return {"reply": text}


@router.post("/twin/summary")
def twin_summary(payload: SummaryRequest):
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
