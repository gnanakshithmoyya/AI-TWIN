from app.rules import evaluate_health


def get_signal(out, name):
    return next(sig for sig in out["signals"] if sig["name"] == name)


def test_vitamin_d_deficiency():
    out = evaluate_health({"vitamin_d": 15})
    vitd = get_signal(out, "Vitamin D")
    assert vitd["status"] == "deficient"
    assert any("supplementation" in rec.lower() for rec in out["recommendations"])


def test_bmi_obesity_flag():
    out = evaluate_health({"bmi": 32})
    bmi = get_signal(out, "BMI")
    assert bmi["status"] == "obesity"
    assert "cardiometabolic_risk" in out["risks"]
