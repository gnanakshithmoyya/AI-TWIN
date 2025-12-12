from app.rules import evaluate_health


def get_signal(out, name):
    return next(sig for sig in out["signals"] if sig["name"] == name)


def test_high_stress_recommendation():
    out = evaluate_health({"stress_level": 9})
    stress = get_signal(out, "Stress")
    assert stress["status"] == "high_stress"
    assert any("stress" in rec.lower() for rec in out["recommendations"])
