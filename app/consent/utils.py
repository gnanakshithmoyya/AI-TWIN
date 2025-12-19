from __future__ import annotations
from typing import Dict, Set

ALL_SCOPES = {
    "profile_basic",
    "chat_history",
    "memory_personalization",
    "sleep_data",
    "activity_data",
    "heart_rate_data",
    "glucose_data",
    "future_wearables",
}


def scopes_for_health_state(health_state: Dict) -> Set[str]:
    scopes = set()
    if not isinstance(health_state, dict):
        return scopes
    if "sleep_hours" in health_state:
        scopes.add("sleep_data")
    if "activity_minutes" in health_state:
        scopes.add("activity_data")
    if "bp_systolic" in health_state or "bp_diastolic" in health_state or "heart_rate" in health_state:
        scopes.add("heart_rate_data")
    if "fasting_glucose" in health_state:
        scopes.add("glucose_data")
    # future fields for wearables would map to future_wearables
    return scopes
