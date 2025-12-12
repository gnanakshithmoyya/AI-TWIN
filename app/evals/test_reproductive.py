from app.rules import evaluate_health


def get_signal(out, name):
    return next(sig for sig in out["signals"] if sig["name"] == name)


def test_long_cycle_and_missed_periods():
    out = evaluate_health({"cycle_length_days": 40, "periods_missed": 2})
    cycle = get_signal(out, "Menstrual Cycle")
    assert cycle["status"] == "long_cycle"
    assert any("missed cycles" in flag.lower() for flag in out["doctor_flags"])
