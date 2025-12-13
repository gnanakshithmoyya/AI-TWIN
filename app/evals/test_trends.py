from app.rules import evaluate_health


def get_signal(out, name):
    return next(sig for sig in out["signals"] if sig["name"] == name)


def test_glucose_trend_improving_and_explanation():
    out = evaluate_health(
        {
            "fasting_glucose": 118,
            "history": {"fasting_glucose": [132, 125]},
        }
    )
    fg = get_signal(out, "Fasting Glucose")
    assert fg["status"] == "prediabetes_range"
    assert fg["explanation"]["rule"].startswith("Prediabetes")
    assert "100-125" in fg["explanation"]["threshold"]
    assert fg["trend"]["direction"] == "improving"
    assert "132" in fg["trend"]["explanation"] and "118" in fg["trend"]["explanation"]


def test_no_trend_without_history():
    out = evaluate_health({"fasting_glucose": 118})
    fg = get_signal(out, "Fasting Glucose")
    assert "trend" not in fg
