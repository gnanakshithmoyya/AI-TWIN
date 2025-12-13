from app.rules import evaluate_health


def get_signal(out, name):
    return next(sig for sig in out["signals"] if sig["name"] == name)


def test_trend_includes_confidence_and_recency_explanation():
    out = evaluate_health(
        {
            "ldl": 145,
            "history": {"ldl": [170, 160, 150]},
        }
    )
    sig = get_signal(out, "LDL")
    assert "trend" in sig
    assert sig["trend"]["direction"] == "improving"
    assert isinstance(sig["trend"]["confidence"], int)
    assert "Recent readings weighted more" in sig["trend"]["explanation"]


def test_recent_improvement_outweighs_older_worse():
    out = evaluate_health(
        {
            "fasting_glucose": 118,
            "history": {"fasting_glucose": [150, 145, 160]},
        }
    )
    sig = get_signal(out, "Fasting Glucose")
    assert sig["trend"]["direction"] == "improving"


def test_sparkline_present_and_direction():
    out = evaluate_health(
        {
            "triglycerides": 180,
            "history": {"triglycerides": [200, 190]},
        }
    )
    sig = get_signal(out, "Triglycerides")
    assert "sparkline" in sig
    assert sig["sparkline"]["values"] == [200, 190, 180]
    assert sig["sparkline"]["direction"] == "down"
