from typing import Any, Dict, List


def evaluate_health(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic rules engine for V1. Accepts a raw dict of health inputs.
    Keys are optional; rules only fire when data is present.
    """
    signals: List[Dict[str, Any]] = []
    risks = set()
    recommendations = set()
    doctor_flags = set()

    def add_signal(name: str, value: Any, status: str, severity: str, details: str = ""):
        signals.append({
            "name": name,
            "value": value,
            "status": status,
            "severity": severity,
            "details": details,
        })

    # --- Metabolic: Fasting glucose ---
    glucose = raw.get("fasting_glucose")
    if glucose is not None:
        if glucose < 100:
            status = "normal"
            severity = "low"
        elif 100 <= glucose <= 125:
            status = "prediabetes_range"
            severity = "moderate"
            risks.add("insulin_resistance")
            recommendations.add("Light physical activity after meals")
            recommendations.add("Reduce refined sugar intake")
        else:
            status = "diabetes_range"
            severity = "high"
            doctor_flags.add("Consult a doctor for diabetes evaluation")
            risks.add("type_2_diabetes_risk")
            recommendations.add("Schedule medical review for glucose")

        add_signal("Fasting Glucose", glucose, status, severity)

    # --- Cardiovascular: Blood pressure ---
    sys_bp = raw.get("bp_systolic")
    dia_bp = raw.get("bp_diastolic")
    if sys_bp is not None and dia_bp is not None:
        status = "normal"
        severity = "low"
        details = "Blood pressure in healthy range"

        if sys_bp < 120 and dia_bp < 80:
            status = "normal"
            severity = "low"
            details = "Below 120/80"
        elif 120 <= sys_bp <= 129 and dia_bp < 80:
            status = "elevated"
            severity = "low"
            details = "120-129 systolic, diastolic <80"
            recommendations.add("Monitor blood pressure and reduce sodium")
        elif 130 <= sys_bp <= 139 or 80 <= dia_bp <= 89:
            status = "stage_1_hypertension"
            severity = "moderate"
            details = "130-139 systolic or 80-89 diastolic"
            risks.add("cardiovascular_risk")
            recommendations.add("Lifestyle changes for blood pressure (salt, activity, weight)")
        elif 140 <= sys_bp <= 180 or 90 <= dia_bp <= 120:
            status = "stage_2_hypertension"
            severity = "high"
            details = "140-180 systolic or 90-120 diastolic"
            risks.add("cardiovascular_risk")
            doctor_flags.add("Discuss blood pressure management with a clinician")
            recommendations.add("Consistent home BP monitoring")
        elif sys_bp > 180 or dia_bp > 120:
            status = "hypertensive_crisis"
            severity = "critical"
            details = ">180 systolic or >120 diastolic"
            risks.add("cardiovascular_risk")
            doctor_flags.add("Seek urgent care for severe blood pressure reading")
        add_signal("Blood Pressure", {"systolic": sys_bp, "diastolic": dia_bp}, status, severity, details)

    # --- Lipids ---
    total_chol = raw.get("total_cholesterol")
    if total_chol is not None:
        if total_chol < 200:
            add_signal("Total Cholesterol", total_chol, "desirable", "low")
        elif 200 <= total_chol <= 239:
            add_signal("Total Cholesterol", total_chol, "borderline_high", "moderate")
            risks.add("cardiovascular_risk")
            recommendations.add("Increase soluble fiber and reduce saturated fat")
        else:
            add_signal("Total Cholesterol", total_chol, "high", "high")
            risks.add("cardiovascular_risk")
            recommendations.add("Review lipid profile with a clinician")

    ldl = raw.get("ldl")
    if ldl is not None:
        if ldl < 100:
            add_signal("LDL", ldl, "optimal", "low")
        elif 100 <= ldl <= 129:
            add_signal("LDL", ldl, "near_optimal", "low")
        elif 130 <= ldl <= 159:
            add_signal("LDL", ldl, "borderline_high", "moderate")
            risks.add("cardiovascular_risk")
            recommendations.add("Dietary adjustments to lower LDL")
        elif 160 <= ldl <= 189:
            add_signal("LDL", ldl, "high", "high")
            risks.add("cardiovascular_risk")
            doctor_flags.add("Consider medical review for high LDL")
        else:
            add_signal("LDL", ldl, "very_high", "high")
            risks.add("cardiovascular_risk")
            doctor_flags.add("High LDL requires medical follow-up")

    hdl = raw.get("hdl")
    if hdl is not None:
        if hdl < 40:
            add_signal("HDL", hdl, "low", "moderate", "Low protective HDL")
            risks.add("cardiovascular_risk")
            recommendations.add("Increase physical activity to raise HDL")
        elif hdl >= 60:
            add_signal("HDL", hdl, "protective", "low")
        else:
            add_signal("HDL", hdl, "acceptable", "low")

    triglycerides = raw.get("triglycerides")
    if triglycerides is not None:
        if triglycerides < 150:
            add_signal("Triglycerides", triglycerides, "normal", "low")
        elif 150 <= triglycerides <= 199:
            add_signal("Triglycerides", triglycerides, "borderline_high", "moderate")
            recommendations.add("Reduce refined carbs and alcohol")
        elif 200 <= triglycerides <= 499:
            add_signal("Triglycerides", triglycerides, "high", "high")
            risks.add("cardiovascular_risk")
            doctor_flags.add("High triglycerides — discuss with clinician")
        else:
            add_signal("Triglycerides", triglycerides, "very_high", "critical")
            risks.add("cardiovascular_risk")
            doctor_flags.add("Very high triglycerides — seek medical review")

    # --- Sleep ---
    sleep_hours = raw.get("sleep_hours")
    if sleep_hours is not None:
        if sleep_hours < 5:
            add_signal("Sleep Duration", sleep_hours, "severe_sleep_debt", "high")
            risks.add("sleep_deprivation_risk")
            recommendations.add("Prioritize sleep extension and consistent schedule")
        elif 5 <= sleep_hours < 7:
            add_signal("Sleep Duration", sleep_hours, "insufficient_sleep", "moderate")
            recommendations.add("Aim for 7-9 hours with consistent bedtime")
        elif 7 <= sleep_hours <= 9:
            add_signal("Sleep Duration", sleep_hours, "optimal", "low")
        else:
            add_signal("Sleep Duration", sleep_hours, "long_sleep", "context")
            recommendations.add("Review long sleep if accompanied by fatigue")

    # --- Activity ---
    activity_minutes = raw.get("activity_minutes")
    if activity_minutes is not None:
        if activity_minutes < 20:
            add_signal("Activity", activity_minutes, "sedentary", "moderate")
            recommendations.add("Light walks after meals")
        elif 20 <= activity_minutes < 40:
            add_signal("Activity", activity_minutes, "light", "moderate")
            recommendations.add("Build toward 40-60 minutes most days")
        elif 40 <= activity_minutes <= 60:
            add_signal("Activity", activity_minutes, "moderate", "low")
        else:
            add_signal("Activity", activity_minutes, "active", "low")

    # --- Nutrition / labs ---
    bmi = raw.get("bmi")
    if bmi is not None:
        if bmi < 18.5:
            add_signal("BMI", bmi, "underweight", "context")
            recommendations.add("Discuss nutrition to reach healthy weight")
        elif 18.5 <= bmi < 25:
            add_signal("BMI", bmi, "normal", "low")
        elif 25 <= bmi < 30:
            add_signal("BMI", bmi, "overweight", "moderate")
            recommendations.add("Focus on gradual weight loss and activity")
        else:
            add_signal("BMI", bmi, "obesity", "high")
            risks.add("cardiometabolic_risk")
            recommendations.add("Structured weight plan with clinician input")

    vitamin_d = raw.get("vitamin_d")
    if vitamin_d is not None:
        if vitamin_d < 20:
            add_signal("Vitamin D", vitamin_d, "deficient", "moderate")
            recommendations.add("Discuss supplementation with clinician")
        elif 20 <= vitamin_d < 30:
            add_signal("Vitamin D", vitamin_d, "insufficient", "moderate")
            recommendations.add("Increase safe sunlight or dietary vitamin D")
        else:
            add_signal("Vitamin D", vitamin_d, "adequate", "low")

    vitamin_b12 = raw.get("vitamin_b12")
    if vitamin_b12 is not None:
        if vitamin_b12 < 200:
            add_signal("Vitamin B12", vitamin_b12, "deficient", "moderate")
            recommendations.add("Assess B12 intake or absorption with clinician")
        elif 200 <= vitamin_b12 < 300:
            add_signal("Vitamin B12", vitamin_b12, "borderline_low", "moderate")
            recommendations.add("Increase B12 sources and recheck")
        else:
            add_signal("Vitamin B12", vitamin_b12, "adequate", "low")

    ferritin = raw.get("ferritin")
    if ferritin is not None:
        if ferritin < 30:
            add_signal("Ferritin", ferritin, "low", "moderate")
            risks.add("iron_deficiency_risk")
            recommendations.add("Check iron intake and discuss with clinician")
        elif ferritin > 400:
            add_signal("Ferritin", ferritin, "high", "moderate")
            doctor_flags.add("High ferritin — consider clinical evaluation")
        else:
            add_signal("Ferritin", ferritin, "normal", "low")

    # --- Reproductive health ---
    cycle_length = raw.get("cycle_length_days")
    periods_missed = raw.get("periods_missed")
    cycle_irregular = raw.get("cycle_irregular")
    if cycle_length is not None:
        if cycle_length < 21:
            add_signal("Menstrual Cycle", cycle_length, "very_short_cycle", "moderate")
            recommendations.add("Track cycles; consider clinician review")
        elif 21 <= cycle_length <= 35:
            add_signal("Menstrual Cycle", cycle_length, "regular_cycle_range", "low")
        elif cycle_length > 35:
            add_signal("Menstrual Cycle", cycle_length, "long_cycle", "moderate")
            recommendations.add("Irregular or long cycles — monitor and consult if persistent")
    if periods_missed is not None and periods_missed >= 2:
        add_signal("Periods Missed", periods_missed, "missed_cycles", "moderate")
        doctor_flags.add("Multiple missed cycles — consider medical evaluation")
    if cycle_irregular:
        add_signal("Cycle Regularity", "irregular", "irregular_cycles", "moderate")
        recommendations.add("Track cycles and discuss patterns with clinician")

    # --- Mental / lifestyle ---
    stress_level = raw.get("stress_level")
    if stress_level is not None:
        if stress_level > 7:
            add_signal("Stress", stress_level, "high_stress", "moderate")
            recommendations.add("Short daily stress-reduction practice")
        elif 5 <= stress_level <= 7:
            add_signal("Stress", stress_level, "moderate_stress", "moderate")
        else:
            add_signal("Stress", stress_level, "manageable_stress", "low")

    mood_variability = raw.get("mood_variability")
    if mood_variability is not None:
        if mood_variability > 7:
            add_signal("Mood Variability", mood_variability, "high_variability", "moderate")
            recommendations.add("Keep a brief mood log and seek support if worsening")
        elif 4 <= mood_variability <= 7:
            add_signal("Mood Variability", mood_variability, "some_variability", "context")
        else:
            add_signal("Mood Variability", mood_variability, "stable", "low")

    return {
        "signals": signals,
        "risks": sorted(risks),
        "recommendations": sorted(recommendations),
        "doctor_flags": sorted(doctor_flags),
    }
