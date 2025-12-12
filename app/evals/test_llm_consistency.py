# app/evals/test_llm_consistency.py
import os
import pytest
import ollama

from app.rules import evaluate_health
from app.rag.loader import load_docs
from app.rag.retriever import retrieve

def local_twin_chat(question: str, raw_health: dict) -> str:
    health_state = evaluate_health(raw_health)
    medical_docs = retrieve(question + str(health_state), top_k=3)

    prompt = f"""
You are a caring health assistant.
You DO NOT invent medical facts.
You ONLY explain the provided health state and references.

HEALTH STATE (FACTS):
{health_state}

MEDICAL REFERENCES:
{medical_docs}

USER QUESTION:
{question}
""".strip()

    resp = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp["message"]["content"]

@pytest.mark.skipif(
    os.getenv("RUN_OLLAMA_EVALS") != "1",
    reason="Set RUN_OLLAMA_EVALS=1 to run slow Ollama integration tests."
)
def test_prediabetes_language():
    load_docs()  # ensure RAG docs are loaded for retrieval
    reply = local_twin_chat("What does my glucose mean?", {"fasting_glucose": 118}).lower()

    assert "prediabetes" in reply
    assert "insulin efficient" not in reply  # prevents the earlier wrong phrasing