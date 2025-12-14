from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import List


class Intent(str, Enum):
    SLEEP_RECAP = "SLEEP_RECAP"
    LAB_EXPLANATION = "LAB_EXPLANATION"
    RISK_EXPLANATION = "RISK_EXPLANATION"
    ACTION_PLAN = "ACTION_PLAN"
    TREND_CHECK = "TREND_CHECK"
    SAFETY_MEDICATION = "SAFETY_MEDICATION"
    DIAGNOSIS_REQUEST = "DIAGNOSIS_REQUEST"
    GENERAL_CHAT = "GENERAL_CHAT"


@dataclass
class IntentResult:
    intent: Intent
    confidence: float
    matched_keywords: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
