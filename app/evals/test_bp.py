from app.rules import evaluate_health


def get_signal(out, name):
    return next(sig for sig in out["signals"] if sig["name"] == name)


def test_bp_normal():
    out = evaluate_health({"bp_systolic": 118, "bp_diastolic": 76})
    bp = get_signal(out, "Blood Pressure")
    assert bp["status"] == "normal"
    assert bp["severity"] == "low"


def test_bp_stage_two_escalation():
    out = evaluate_health({"bp_systolic": 150, "bp_diastolic": 95})
    bp = get_signal(out, "Blood Pressure")
    assert bp["status"] == "stage_2_hypertension"
    assert any("blood pressure" in flag.lower() for flag in out["doctor_flags"])
