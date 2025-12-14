from __future__ import annotations
from typing import Dict, Any, List, Tuple
from app.intent.schema import Intent, IntentResult


INTENT_KEYWORDS: List[Tuple[Intent, List[str]]] = [
    (Intent.SLEEP_RECAP, ["sleep", "asleep", "rest"]),
    (Intent.LAB_EXPLANATION, ["ldl", "hdl", "cholesterol", "triglyceride", "glucose", "lab", "test"]),
    (Intent.RISK_EXPLANATION, ["danger", "risky", "risk", "concern"]),
    (Intent.ACTION_PLAN, ["what should i do", "next step", "improve", "fix", "better"]),
    (Intent.TREND_CHECK, ["trend", "improving", "worse", "getting better", "progress"]),
    (Intent.SAFETY_MEDICATION, ["med", "medication", "dose", "insulin", "pill", "tablet", "stop", "start"]),
    (Intent.DIAGNOSIS_REQUEST, ["do i have", "am i", "diagnose", "diagnosis"]),
]


INTENT_REQUIRED_FIELDS = {
    Intent.SLEEP_RECAP: ["Sleep Duration"],
    Intent.LAB_EXPLANATION: [],
    Intent.RISK_EXPLANATION: [],
    Intent.ACTION_PLAN: [],
    Intent.TREND_CHECK: [],
    Intent.SAFETY_MEDICATION: [],
    Intent.DIAGNOSIS_REQUEST: [],
    Intent.GENERAL_CHAT: [],
}


def classify_intent(question: str, health_state: Dict[str, Any]) -> IntentResult:
    q = (question or "").lower()
    matched: List[str] = []
    chosen = Intent.GENERAL_CHAT
    confidence = 0.5

    for intent, keywords in INTENT_KEYWORDS:
        hits = [kw for kw in keywords if kw in q]
        if hits:
            matched.extend(hits)
            chosen = intent
            confidence = 0.9 if len(hits) >= 2 else 0.75
            break

    required = INTENT_REQUIRED_FIELDS.get(chosen, [])
    # Build presence map based on signal names we expect evaluate_health to emit
    signals_present = set()
    if isinstance(health_state, dict):
        for key in health_state.keys():
            signals_present.add(key.lower())

    missing = []
    for field_name in required:
        # map friendly names to expected health_state keys
        if field_name == "Sleep Duration":
            if "sleep_hours" not in signals_present:
                missing.append(field_name)

    return IntentResult(
        intent=chosen,
        confidence=confidence,
        matched_keywords=matched,
        required_fields=required,
        missing_fields=missing,
    )
