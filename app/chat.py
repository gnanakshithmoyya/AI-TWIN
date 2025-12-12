# app/chat.py

from fastapi import APIRouter
from pydantic import BaseModel
from app.rules import evaluate_health
from app.rag.retriever import retrieve
import ollama

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    health_state: dict


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
    health_state = evaluate_health(payload.health_state)
    medical_docs = retrieve(payload.question + str(health_state))
    if medical_docs:
        references = "\n\n".join(medical_docs)
    else:
        references = "No specific references retrieved. Stay within provided health facts."

    prompt = f"""
You are a caring, safety-first health assistant.
Rules:
- Do NOT invent medical facts or thresholds.
- Do NOT diagnose.
- Base every statement on HEALTH STATE and MEDICAL REFERENCES.
- If references are limited, keep guidance high-level and encourage clinician review for concerns.

HEALTH STATE (FACTS):
{health_state}

MEDICAL REFERENCES:
{references}

USER QUESTION:
{payload.question}
""".strip()

    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}]
    )

    return {"reply": response["message"]["content"]}


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
    return evaluate_health(combined)
