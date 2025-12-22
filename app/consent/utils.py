from __future__ import annotations
from typing import Dict, Set

ALL_SCOPES = {
    "profile_basic",
    "chat_history",
    "memory_personalization",
    "sleep_data",
    "activity_data",
    "steps_activity_data",
    "heart_rate_data",
    "glucose_data",
    "future_wearables",
    "wearables_connect",
    "wearables_sync",
    "wearables_background_sync",
    "hrv_data",
    "spo2_data",
    "temperature_data",
    "body_data",
    "vo2max_data",
    "stress_data",
    "readiness_data",
    "blood_pressure_data",
    "glucose_cgm_data",
    "cycle_tracking_data",
}


def scopes_for_health_state(health_state: Dict) -> Set[str]:
    scopes = set()
    if not isinstance(health_state, dict):
        return scopes
    if "sleep_hours" in health_state:
        scopes.add("sleep_data")
    if "activity_minutes" in health_state or "activity_steps" in health_state or "calories_burned" in health_state:
        scopes.add("activity_data")
    if "bp_systolic" in health_state or "bp_diastolic" in health_state or "heart_rate" in health_state or "resting_heart_rate" in health_state:
        scopes.add("heart_rate_data")
    if "fasting_glucose" in health_state or "glucose_cgm" in health_state:
        scopes.add("glucose_data")
    if "glucose_cgm" in health_state:
        scopes.add("glucose_cgm_data")
    if "bp_systolic" in health_state or "bp_diastolic" in health_state:
        scopes.add("blood_pressure_data")
    if "hrv" in health_state:
        scopes.add("hrv_data")
    if "spo2" in health_state:
        scopes.add("spo2_data")
    if "temperature_deviation" in health_state:
        scopes.add("temperature_data")
    if "weight" in health_state or "bmi" in health_state:
        scopes.add("body_data")
    if "vo2max" in health_state:
        scopes.add("vo2max_data")
    if "stress_score" in health_state:
        scopes.add("stress_data")
    if "readiness_score" in health_state:
        scopes.add("readiness_data")
    if "cycle_tracking" in health_state:
        scopes.add("cycle_tracking_data")
    # future fields for wearables would map to future_wearables
    return scopes
