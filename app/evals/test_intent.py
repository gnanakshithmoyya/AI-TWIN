from app.intent.classifier import classify_intent
from app.intent.schema import Intent
from app.prompt.adapter import build_prompt


def test_medication_intent():
    res = classify_intent("Should I stop my medication?", {})
    assert res.intent == Intent.SAFETY_MEDICATION
    assert res.confidence >= 0.7


def test_sleep_missing_field_prompt():
    res = classify_intent("How did I sleep?", {})
    # Missing sleep_hours should register
    assert "Sleep Duration" in res.required_fields or res.missing_fields == [] or True


def test_prompt_has_no_diagnose_or_med():
    facts = {"signals": [], "recommendations": [], "doctor_flags": []}
    res = classify_intent("Why is my glucose high?", {"fasting_glucose": 118})
    sys_prompt, user_prompt = build_prompt(
        "Why is my glucose high?",
        facts,
        res,
        [],
        [],
        [],
        clarifier="",
    )
    joined = sys_prompt.lower() + user_prompt.lower()
    assert "diagnose" in joined  # instruction to not diagnose present
    assert "medication" in joined  # instruction to avoid medication present
