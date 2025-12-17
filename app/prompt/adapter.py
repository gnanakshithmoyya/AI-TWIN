from __future__ import annotations
from typing import Dict, Any, Tuple, List
from app.intent.schema import IntentResult, Intent
from app.safety import DISCLAIMER_TEXT


def _summary_snippets(facts: Dict[str, Any]) -> str:
    parts = []
    for sig in facts.get("signals", []):
        line = f"- {sig.get('name')}: {sig.get('value')} ({sig.get('status')}, {sig.get('severity')})"
        if sig.get("explanation"):
            line += f" | why: {sig['explanation'].get('why_it_matters', '')}"
        if sig.get("trend"):
            trend = sig["trend"]
            line += f" | trend: {trend.get('direction')} (conf {trend.get('confidence')})"
        parts.append(line)
    if facts.get("recommendations"):
        parts.append(f"Recommendations: {facts.get('recommendations')}")
    if facts.get("doctor_flags"):
        parts.append(f"Doctor flags: {facts.get('doctor_flags')}")
    return "\n".join(parts)


def _clarifying_question(intent: IntentResult) -> str:
    if intent.missing_fields:
        need = intent.missing_fields[0]
        return f"Could you share your {need.lower()} so I can be more specific?"
    return ""


def _intent_template(intent: Intent) -> str:
    if intent == Intent.SLEEP_RECAP:
        return (
            "1) Brief sleep recap.\n"
            "2) Why it matters.\n"
            "3) One gentle next step if listed in recommendations.\n"
            "4) One short follow-up question if needed."
        )
    if intent == Intent.LAB_EXPLANATION:
        return "Explain the lab value, what range it is in, and why it matters. Keep it short."
    if intent == Intent.RISK_EXPLANATION:
        return "Summarize the current risks already listed. Be calm and non-alarming."
    if intent == Intent.ACTION_PLAN:
        return "List 1-2 recommendations already provided. Do not invent new advice."
    if intent == Intent.TREND_CHECK:
        return "Describe trend direction if present; otherwise say trend is not available."
    if intent == Intent.SAFETY_MEDICATION:
        return "Refuse to give medication guidance and suggest speaking with a clinician."
    if intent == Intent.DIAGNOSIS_REQUEST:
        return "Explain ranges and say this is not a diagnosis; advise clinician consultation."
    return "Give a concise, friendly explanation based only on the facts."


def build_prompt(
    question: str,
    facts: Dict[str, Any],
    intent_result: IntentResult,
    retrieved_docs: List[str],
    chat_summaries: List[str],
    user_memory_snippets: List[str],
    clarifier: str,
) -> Tuple[str, str]:
    summary = _summary_snippets(facts)
    refs_text = "\n\n".join(retrieved_docs) if retrieved_docs else "NO_REFERENCES_FOUND"
    chat_summaries_text = "\n".join(chat_summaries) if chat_summaries else "None"
    user_memory_text = "\n".join(user_memory_snippets) if user_memory_snippets else "None"

    system_prompt = f"""
You are a health explanation assistant.

NON-NEGOTIABLE RULES:
- Use ONLY the provided FACTS. Do not add new medical facts.
- Do NOT diagnose conditions.
- Do NOT recommend starting/stopping/changing medications.
- Do NOT invent numbers, thresholds, or risks not present in FACTS.
- If the user's question cannot be answered using FACTS, say:
  "I don’t have enough information to answer that safely."

Tone:
- Speak in a natural, calm, human tone — like a supportive health companion.
- Avoid robotic phrases like "based on the provided facts" or "according to the facts."
- Prefer: "Based on the data you shared," "From what I can see here," "Looking at your recent readings."
- Be concise, warm, and conversational. Use contractions where natural.
- Highlight key numbers once, then explain.

Always end with this disclaimer (verbatim):
{DISCLAIMER_TEXT}
""".strip()

    user_prompt = f"""
USER QUESTION:
{question}

INTENT:
{intent_result.intent} (confidence {intent_result.confidence})

FACTS (authoritative):
{summary if summary else "No signals available."}

CHAT SUMMARIES (this chat only, brief):
{chat_summaries_text}

USER MEMORY (user-scoped, brief; no raw values):
{user_memory_text}

MEDICAL REFERENCES (do not contradict FACTS):
{refs_text}

RESPONSE TEMPLATE:
{_intent_template(intent_result.intent)}

CLARIFYING (ask only if needed):
{clarifier or "None"}
""".strip()

    return system_prompt, user_prompt
