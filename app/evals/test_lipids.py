from app.rules import evaluate_health


def get_signal(out, name):
    return next(sig for sig in out["signals"] if sig["name"] == name)


def test_ldl_high_triggers_flag():
    out = evaluate_health({"ldl": 170})
    ldl = get_signal(out, "LDL")
    assert ldl["status"] == "high"
    assert any("ldl" in flag.lower() for flag in out["doctor_flags"])


def test_hdl_low_marks_risk():
    out = evaluate_health({"hdl": 35})
    hdl = get_signal(out, "HDL")
    assert hdl["status"] == "low"
    assert "cardiovascular_risk" in out["risks"]
