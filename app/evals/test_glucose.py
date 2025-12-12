# app/evals/test_glucose.py
from app.rules import evaluate_health

def test_glucose_prediabetes_range():
    out = evaluate_health({"fasting_glucose": 118})
    assert out["signals"], "Expected at least one signal"
    fg = out["signals"][0]
    assert fg["status"] == "prediabetes_range"

def test_glucose_normal_range():
    out = evaluate_health({"fasting_glucose": 90})
    fg = out["signals"][0]
    assert fg["status"] == "normal"