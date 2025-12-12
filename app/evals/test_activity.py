from app.rules import evaluate_health


def get_signal(out, name):
    return next(sig for sig in out["signals"] if sig["name"] == name)


def test_activity_sedentary():
    out = evaluate_health({"activity_minutes": 10})
    activity = get_signal(out, "Activity")
    assert activity["status"] == "sedentary"
    assert any("walks" in rec.lower() for rec in out["recommendations"])
