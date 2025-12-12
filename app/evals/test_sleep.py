from app.rules import evaluate_health


def get_signal(out, name):
    return next(sig for sig in out["signals"] if sig["name"] == name)


def test_sleep_optimal():
    out = evaluate_health({"sleep_hours": 8})
    sleep = get_signal(out, "Sleep Duration")
    assert sleep["status"] == "optimal"
    assert sleep["severity"] == "low"


def test_sleep_severe_debt():
    out = evaluate_health({"sleep_hours": 4.5})
    sleep = get_signal(out, "Sleep Duration")
    assert sleep["status"] == "severe_sleep_debt"
    assert "sleep_deprivation_risk" in out["risks"]
