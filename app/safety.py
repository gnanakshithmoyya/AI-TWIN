from __future__ import annotations
from typing import Dict, Any, Tuple, List
import re

# Block topics that are high-risk for a consumer non-medical app
FORBIDDEN_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(stop|start|change|increase|decrease)\b.*\b(med|medicine|medication|dose|insulin)\b", re.I),
    re.compile(r"\b(what medication|what drug|what dose)\b", re.I),
    re.compile(r"\b(do i have|am i)\b.*\b(diabetes|cancer|stroke|heart attack)\b", re.I),
    re.compile(r"\bdiagnos(e|is)\b", re.I),
    re.compile(r"\bemergency\b|\burgent\b|\bcall 911\b", re.I),
]

# (regex, required_signal_name, safe_message)
MISSING_DATA_RULES = [
    (re.compile(r"\bsleep\b", re.I), "Sleep Duration",
     "I don’t have sleep data for the timeframe you asked about, so I can’t answer that accurately."),
    (re.compile(r"\bglucose\b|\bsugar\b", re.I), "Fasting Glucose",
     "I don’t have glucose data to answer that safely. If you share your fasting glucose value, I can explain it."),
    (re.compile(r"\bbp\b|\bblood pressure\b", re.I), "Blood Pressure",
     "I don’t have blood pressure values (systolic/diastolic) to answer that safely."),
    (re.compile(r"\bldl\b|\bhdl\b|\btriglycerides\b|\bcholesterol\b", re.I), "LDL",
     "I don’t have lipid values to answer that safely. If you share LDL/HDL/triglycerides, I can explain them."),
]

DISCLAIMER_TEXT = (
    "This app provides educational health insights and trends. "
    "It does not diagnose or replace medical advice. "
    "Always consult a qualified healthcare professional."
)


def is_forbidden_question(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    return any(p.search(q) for p in FORBIDDEN_PATTERNS)


def required_signal_present(facts: Dict[str, Any], signal_name: str) -> bool:
    for s in facts.get("signals", []):
        if s.get("name") == signal_name:
            return True
    return False


def check_missing_data(question: str, facts: Dict[str, Any]) -> Tuple[bool, str]:
    q = (question or "").strip()
    for pattern, required_signal, msg in MISSING_DATA_RULES:
        if pattern.search(q) and not required_signal_present(facts, required_signal):
            return True, msg
    return False, ""


def response_mentions_unknown_terms(reply: str, facts: Dict[str, Any]) -> bool:
    # Allowed terms include known signal names; block certain red-flag words regardless.
    allowed_terms = {s.get("name", "").lower() for s in facts.get("signals", [])}
    red_flags = {"cancer", "stroke", "medication", "dose", "emergency"}
    if any(flag in reply.lower() for flag in red_flags):
        return True
    # If the reply mentions a health term not in allowed terms, we treat it cautiously.
    for word in reply.lower().split():
        clean = re.sub(r"[^a-z]", "", word)
        if clean and clean not in allowed_terms and clean in red_flags:
            return True
    return False
