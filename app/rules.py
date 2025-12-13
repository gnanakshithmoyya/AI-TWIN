from typing import Any, Dict, List, Optional, Tuple


def _explanation(rule: str, threshold: str, why: str) -> Dict[str, str]:
    return {
        "rule": rule,
        "threshold": threshold,
        "why_it_matters": why,
    }


def _format_series(values: List[Any]) -> str:
    return " -> ".join(str(v) for v in values)


def _compute_trend(history_values: List[Any], current_value: Any, better_when_lower: bool) -> Optional[Dict[str, Any]]:
    """
    Trend with deterministic confidence and recency weighting.
    More recent differences carry higher weight; tiny changes within tolerance are treated as stable.
    """
    if not history_values:
        return None

    series = history_values + [current_value]
    if len(series) < 2:
        return None

    tolerance = 1  # buffer to ignore very small changes
    diffs = []
    weights = []
    # Weight recent deltas more (linear ramp up to 1.0)
    for i in range(len(series) - 1):
        diff = series[i + 1] - series[i]
        weight = (i + 1) / (len(series) - 1)
        diffs.append(diff)
        weights.append(weight)

    weighted_change = sum(d * w for d, w in zip(diffs, weights))
    if better_when_lower:
        if weighted_change < -tolerance:
            direction = "improving"
        elif weighted_change > tolerance:
            direction = "worsening"
        else:
            direction = "stable"
    else:
        if weighted_change > tolerance:
            direction = "improving"
        elif weighted_change < -tolerance:
            direction = "worsening"
        else:
            direction = "stable"

    # Consistency: how aligned the diffs are with overall direction
    primary_sign = 0
    if direction == "improving":
        primary_sign = -1 if better_when_lower else 1
    elif direction == "worsening":
        primary_sign = 1 if better_when_lower else -1
    valid_diffs = [d for d in diffs if abs(d) > tolerance]
    if valid_diffs and primary_sign != 0:
        aligned = sum(1 for d in valid_diffs if (d > 0 and primary_sign > 0) or (d < 0 and primary_sign < 0))
        consistency_ratio = aligned / len(valid_diffs)
    else:
        consistency_ratio = 0.5  # neutral when limited signal

    # Confidence factors
    data_factor = min(len(series), 5) / 5 * 40  # up to 40 for more points
    consistency_factor = consistency_ratio * 40  # up to 40 for consistent direction
    magnitude_factor = min(abs(weighted_change) / (tolerance * 3), 1) * 20  # up to 20 for larger moves
    confidence = round(min(100, max(10, data_factor + consistency_factor + magnitude_factor)))

    explanation = (
        f"Recent readings weighted more; values: {_format_series(series)}; "
        f"weighted change {round(weighted_change, 1)}"
    )

    return {
        "direction": direction,
        "confidence": confidence,
        "explanation": explanation,
    }


def _sparkline(history_values: List[Any], current_value: Any) -> Dict[str, Any]:
    values = history_values + [current_value]
    if values[-1] < values[0]:
        direction = "down"
    elif values[-1] > values[0]:
        direction = "up"
    else:
        direction = "flat"
    return {"values": values, "direction": direction}


TREND_RULES = {
    "fasting_glucose": True,
    "total_cholesterol": True,
    "ldl": True,
    "hdl": False,  # higher is better
    "triglycerides": True,
    "bmi": True,
}


def evaluate_health(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic rules engine for V1 with explainability and optional trends.
    Accepts a raw dict of health inputs. Keys are optional; rules only fire when present.
    """
    signals: List[Dict[str, Any]] = []
    risks = set()
    recommendations = set()
    doctor_flags = set()

    history_data = raw.get("history") if isinstance(raw.get("history"), dict) else {}

    def get_history(key: str) -> List[Any]:
        values = history_data.get(key) if isinstance(history_data, dict) else None
        if isinstance(values, (list, tuple)):
            return [v for v in values if isinstance(v, (int, float))]
        return []

    def add_signal(
        name: str,
        value: Any,
        status: str,
        severity: str,
        explanation: Dict[str, str],
        details: str = "",
        trend: Optional[Dict[str, str]] = None,
        sparkline: Optional[Dict[str, Any]] = None,
    ):
        entry = {
            "name": name,
            "value": value,
            "status": status,
            "severity": severity,
            "details": details,
            "explanation": explanation,
        }
        if trend:
            entry["trend"] = trend
        if sparkline:
            entry["sparkline"] = sparkline
        signals.append(entry)

    # --- Metabolic: Fasting glucose ---
    glucose = raw.get("fasting_glucose")
    if glucose is not None:
        hist = get_history("fasting_glucose")
        trend = _compute_trend(hist, glucose, TREND_RULES["fasting_glucose"])
        sparkline = _sparkline(hist, glucose) if hist else None
        if glucose < 100:
            status = "normal"
            severity = "low"
            exp = _explanation(
                "Fasting glucose is normal when below 100 mg/dL after an overnight fast.",
                "<100 mg/dL fasting",
                "Normal fasting glucose suggests low current risk for insulin resistance.",
            )
        elif 100 <= glucose <= 125:
            status = "prediabetes_range"
            severity = "moderate"
            risks.add("insulin_resistance")
            recommendations.add("Light physical activity after meals")
            recommendations.add("Reduce refined sugar intake")
            exp = _explanation(
                "Prediabetes is flagged when fasting glucose is between 100 and 125 mg/dL.",
                "100-125 mg/dL fasting",
                "Elevated fasting glucose over time can indicate insulin resistance.",
            )
        else:
            status = "diabetes_range"
            severity = "high"
            doctor_flags.add("Consult a doctor for diabetes evaluation")
            risks.add("type_2_diabetes_risk")
            recommendations.add("Schedule medical review for glucose")
            exp = _explanation(
                "Diabetes-range fasting glucose is 126 mg/dL or higher.",
                ">=126 mg/dL fasting",
                "Sustained high fasting glucose is linked to diabetes complications.",
            )

        add_signal("Fasting Glucose", glucose, status, severity, exp, trend=trend, sparkline=sparkline)

    # --- Cardiovascular: Blood pressure ---
    sys_bp = raw.get("bp_systolic")
    dia_bp = raw.get("bp_diastolic")
    if sys_bp is not None and dia_bp is not None:
        status = "normal"
        severity = "low"
        details = "Blood pressure in healthy range"
        exp = _explanation(
            "Normal blood pressure is below 120 systolic and 80 diastolic.",
            "<120/<80 mmHg",
            "Healthy blood pressure reduces strain on the heart and arteries.",
        )

        if sys_bp < 120 and dia_bp < 80:
            status = "normal"
            severity = "low"
            details = "Below 120/80"
            exp = _explanation(
                "Normal blood pressure is below 120 systolic and 80 diastolic.",
                "<120/<80 mmHg",
                "Healthy blood pressure reduces strain on the heart and arteries.",
            )
        elif 120 <= sys_bp <= 129 and dia_bp < 80:
            status = "elevated"
            severity = "low"
            details = "120-129 systolic, diastolic <80"
            recommendations.add("Monitor blood pressure and reduce sodium")
            exp = _explanation(
                "Elevated blood pressure is 120-129 systolic with diastolic below 80.",
                "120-129 / <80 mmHg",
                "Early elevation can progress; monitoring and lifestyle can help control it.",
            )
        elif 130 <= sys_bp <= 139 or 80 <= dia_bp <= 89:
            status = "stage_1_hypertension"
            severity = "moderate"
            details = "130-139 systolic or 80-89 diastolic"
            risks.add("cardiovascular_risk")
            recommendations.add("Lifestyle changes for blood pressure (salt, activity, weight)")
            exp = _explanation(
                "Stage 1 hypertension is 130-139 systolic or 80-89 diastolic.",
                "130-139 or 80-89 mmHg",
                "Higher pressures raise heart and vessel strain; lifestyle can reduce risk.",
            )
        elif 140 <= sys_bp <= 180 or 90 <= dia_bp <= 120:
            status = "stage_2_hypertension"
            severity = "high"
            details = "140-180 systolic or 90-120 diastolic"
            risks.add("cardiovascular_risk")
            doctor_flags.add("Discuss blood pressure management with a clinician")
            recommendations.add("Consistent home BP monitoring")
            exp = _explanation(
                "Stage 2 hypertension is 140-180 systolic or 90-120 diastolic.",
                "140-180 or 90-120 mmHg",
                "Sustained high pressure meaningfully increases cardiovascular risk.",
            )
        elif sys_bp > 180 or dia_bp > 120:
            status = "hypertensive_crisis"
            severity = "critical"
            details = ">180 systolic or >120 diastolic"
            risks.add("cardiovascular_risk")
            doctor_flags.add("Seek urgent care for severe blood pressure reading")
            exp = _explanation(
                "Hypertensive crisis is when systolic is over 180 or diastolic over 120.",
                ">180 or >120 mmHg",
                "This level can cause organ damage; urgent care is recommended.",
            )
        add_signal("Blood Pressure", {"systolic": sys_bp, "diastolic": dia_bp}, status, severity, exp, details)

    # --- Lipids ---
    total_chol = raw.get("total_cholesterol")
    if total_chol is not None:
        hist = get_history("total_cholesterol")
        trend = _compute_trend(hist, total_chol, TREND_RULES["total_cholesterol"])
        sparkline = _sparkline(hist, total_chol) if hist else None
        if total_chol < 200:
            exp = _explanation(
                "Desirable total cholesterol is below 200 mg/dL.",
                "<200 mg/dL",
                "Lower total cholesterol is generally linked to lower cardiovascular risk.",
            )
            add_signal("Total Cholesterol", total_chol, "desirable", "low", exp, trend=trend, sparkline=sparkline)
        elif 200 <= total_chol <= 239:
            risks.add("cardiovascular_risk")
            recommendations.add("Increase soluble fiber and reduce saturated fat")
            exp = _explanation(
                "Borderline high total cholesterol is 200-239 mg/dL.",
                "200-239 mg/dL",
                "Elevated cholesterol can contribute to plaque buildup over time.",
            )
            add_signal("Total Cholesterol", total_chol, "borderline_high", "moderate", exp, trend=trend, sparkline=sparkline)
        else:
            risks.add("cardiovascular_risk")
            recommendations.add("Review lipid profile with a clinician")
            exp = _explanation(
                "High total cholesterol is 240 mg/dL or higher.",
                ">=240 mg/dL",
                "High cholesterol increases cardiovascular risk and may need treatment.",
            )
            add_signal("Total Cholesterol", total_chol, "high", "high", exp, trend=trend, sparkline=sparkline)

    ldl = raw.get("ldl")
    if ldl is not None:
        hist = get_history("ldl")
        trend = _compute_trend(hist, ldl, TREND_RULES["ldl"])
        sparkline = _sparkline(hist, ldl) if hist else None
        if ldl < 100:
            exp = _explanation(
                "Optimal LDL is below 100 mg/dL.",
                "<100 mg/dL",
                "Lower LDL means less LDL available to form arterial plaque.",
            )
            add_signal("LDL", ldl, "optimal", "low", exp, trend=trend, sparkline=sparkline)
        elif 100 <= ldl <= 129:
            exp = _explanation(
                "Near-optimal LDL is 100-129 mg/dL.",
                "100-129 mg/dL",
                "Staying below 130 keeps LDL-related risk lower.",
            )
            add_signal("LDL", ldl, "near_optimal", "low", exp, trend=trend, sparkline=sparkline)
        elif 130 <= ldl <= 159:
            risks.add("cardiovascular_risk")
            recommendations.add("Dietary adjustments to lower LDL")
            exp = _explanation(
                "Borderline high LDL is 130-159 mg/dL.",
                "130-159 mg/dL",
                "Higher LDL can accelerate plaque buildup over time.",
            )
            add_signal("LDL", ldl, "borderline_high", "moderate", exp, trend=trend, sparkline=sparkline)
        elif 160 <= ldl <= 189:
            risks.add("cardiovascular_risk")
            doctor_flags.add("Consider medical review for high LDL")
            exp = _explanation(
                "High LDL is 160-189 mg/dL.",
                "160-189 mg/dL",
                "High LDL is linked to higher cardiovascular risk; review with a clinician.",
            )
            add_signal("LDL", ldl, "high", "high", exp, trend=trend, sparkline=sparkline)
        else:
            risks.add("cardiovascular_risk")
            doctor_flags.add("High LDL requires medical follow-up")
            exp = _explanation(
                "Very high LDL is 190 mg/dL or above.",
                ">=190 mg/dL",
                "Very high LDL carries significant cardiovascular risk.",
            )
            add_signal("LDL", ldl, "very_high", "high", exp, trend=trend, sparkline=sparkline)

    hdl = raw.get("hdl")
    if hdl is not None:
        hist = get_history("hdl")
        trend = _compute_trend(hist, hdl, TREND_RULES["hdl"])
        sparkline = _sparkline(hist, hdl) if hist else None
        if hdl < 40:
            risks.add("cardiovascular_risk")
            recommendations.add("Increase physical activity to raise HDL")
            exp = _explanation(
                "Low HDL is below 40 mg/dL.",
                "<40 mg/dL",
                "Lower HDL means less protective cholesterol transport.",
            )
            add_signal("HDL", hdl, "low", "moderate", exp, "Low protective HDL", trend=trend, sparkline=sparkline)
        elif hdl >= 60:
            exp = _explanation(
                "HDL of 60 mg/dL or higher is considered protective.",
                ">=60 mg/dL",
                "Higher HDL helps remove cholesterol from arteries.",
            )
            add_signal("HDL", hdl, "protective", "low", exp, trend=trend, sparkline=sparkline)
        else:
            exp = _explanation(
                "Acceptable HDL is between 40 and 59 mg/dL.",
                "40-59 mg/dL",
                "HDL in this range provides some protective effect.",
            )
            add_signal("HDL", hdl, "acceptable", "low", exp, trend=trend, sparkline=sparkline)

    triglycerides = raw.get("triglycerides")
    if triglycerides is not None:
        hist = get_history("triglycerides")
        trend = _compute_trend(hist, triglycerides, TREND_RULES["triglycerides"])
        sparkline = _sparkline(hist, triglycerides) if hist else None
        if triglycerides < 150:
            exp = _explanation(
                "Normal triglycerides are below 150 mg/dL.",
                "<150 mg/dL",
                "Normal triglycerides are linked to lower cardiovascular risk.",
            )
            add_signal("Triglycerides", triglycerides, "normal", "low", exp, trend=trend, sparkline=sparkline)
        elif 150 <= triglycerides <= 199:
            recommendations.add("Reduce refined carbs and alcohol")
            exp = _explanation(
                "Borderline high triglycerides are 150-199 mg/dL.",
                "150-199 mg/dL",
                "Higher triglycerides can contribute to metabolic and cardiovascular risk.",
            )
            add_signal("Triglycerides", triglycerides, "borderline_high", "moderate", exp, trend=trend, sparkline=sparkline)
        elif 200 <= triglycerides <= 499:
            risks.add("cardiovascular_risk")
            doctor_flags.add("High triglycerides - discuss with clinician")
            exp = _explanation(
                "High triglycerides are 200-499 mg/dL.",
                "200-499 mg/dL",
                "Elevated triglycerides increase cardiovascular risk and may need treatment.",
            )
            add_signal("Triglycerides", triglycerides, "high", "high", exp, trend=trend, sparkline=sparkline)
        else:
            risks.add("cardiovascular_risk")
            doctor_flags.add("Very high triglycerides - seek medical review")
            exp = _explanation(
                "Very high triglycerides are 500 mg/dL or higher.",
                ">=500 mg/dL",
                "Very high triglycerides raise pancreatitis and cardiovascular risk.",
            )
            add_signal("Triglycerides", triglycerides, "very_high", "critical", exp, trend=trend, sparkline=sparkline)

    # --- Sleep ---
    sleep_hours = raw.get("sleep_hours")
    if sleep_hours is not None:
        if sleep_hours < 5:
            risks.add("sleep_deprivation_risk")
            recommendations.add("Prioritize sleep extension and consistent schedule")
            exp = _explanation(
                "Severe sleep debt when sleep is under 5 hours.",
                "<5 hours",
                "Very short sleep impairs cognition, metabolism, and cardiovascular health.",
            )
            add_signal("Sleep Duration", sleep_hours, "severe_sleep_debt", "high", exp)
        elif 5 <= sleep_hours < 7:
            recommendations.add("Aim for 7-9 hours with consistent bedtime")
            exp = _explanation(
                "Sleep under 7 hours is considered insufficient for most adults.",
                "5-6 hours",
                "Insufficient sleep can affect mood, glucose, and blood pressure.",
            )
            add_signal("Sleep Duration", sleep_hours, "insufficient_sleep", "moderate", exp)
        elif 7 <= sleep_hours <= 9:
            exp = _explanation(
                "Optimal sleep for most adults is 7-9 hours.",
                "7-9 hours",
                "Adequate sleep supports recovery, mood, and metabolic health.",
            )
            add_signal("Sleep Duration", sleep_hours, "optimal", "low", exp)
        else:
            recommendations.add("Review long sleep if accompanied by fatigue")
            exp = _explanation(
                "Long sleep is above 9 hours for most adults.",
                ">9 hours",
                "Long sleep can be normal for some but may signal underlying issues if new.",
            )
            add_signal("Sleep Duration", sleep_hours, "long_sleep", "context", exp)

    # --- Activity ---
    activity_minutes = raw.get("activity_minutes")
    if activity_minutes is not None:
        if activity_minutes < 20:
            recommendations.add("Light walks after meals")
            exp = _explanation(
                "Sedentary when activity is under ~20 minutes per day.",
                "<20 minutes/day",
                "Very low activity can worsen metabolic and cardiovascular health.",
            )
            add_signal("Activity", activity_minutes, "sedentary", "moderate", exp)
        elif 20 <= activity_minutes < 40:
            recommendations.add("Build toward 40-60 minutes most days")
            exp = _explanation(
                "Light activity around 20-39 minutes per day.",
                "20-39 minutes/day",
                "Gradually increasing activity improves cardiovascular and metabolic health.",
            )
            add_signal("Activity", activity_minutes, "light", "moderate", exp)
        elif 40 <= activity_minutes <= 60:
            exp = _explanation(
                "Moderate activity around 40-60 minutes per day.",
                "40-60 minutes/day",
                "Consistent moderate activity supports heart and glucose health.",
            )
            add_signal("Activity", activity_minutes, "moderate", "low", exp)
        else:
            exp = _explanation(
                "Active when exceeding ~60 minutes per day.",
                ">60 minutes/day",
                "Higher activity levels generally support cardiovascular health.",
            )
            add_signal("Activity", activity_minutes, "active", "low", exp)

    # --- Nutrition / labs ---
    bmi = raw.get("bmi")
    if bmi is not None:
        hist = get_history("bmi")
        trend = _compute_trend(hist, bmi, TREND_RULES["bmi"])
        sparkline = _sparkline(hist, bmi) if hist else None
        if bmi < 18.5:
            recommendations.add("Discuss nutrition to reach healthy weight")
            exp = _explanation(
                "BMI under 18.5 is considered underweight.",
                "<18.5",
                "Underweight BMI can be associated with nutrient gaps and low reserves.",
            )
            add_signal("BMI", bmi, "underweight", "context", exp, trend=trend, sparkline=sparkline)
        elif 18.5 <= bmi < 25:
            exp = _explanation(
                "BMI 18.5-24.9 is considered normal weight range.",
                "18.5-24.9",
                "Normal BMI is linked with lower cardiometabolic risk on average.",
            )
            add_signal("BMI", bmi, "normal", "low", exp, trend=trend, sparkline=sparkline)
        elif 25 <= bmi < 30:
            recommendations.add("Focus on gradual weight loss and activity")
            exp = _explanation(
                "BMI 25-29.9 is categorized as overweight.",
                "25-29.9",
                "Higher BMI can increase cardiometabolic risk over time.",
            )
            add_signal("BMI", bmi, "overweight", "moderate", exp, trend=trend, sparkline=sparkline)
        else:
            risks.add("cardiometabolic_risk")
            recommendations.add("Structured weight plan with clinician input")
            exp = _explanation(
                "BMI 30 or higher is categorized as obesity.",
                ">=30",
                "Obesity is linked with higher cardiometabolic risk; structured support helps.",
            )
            add_signal("BMI", bmi, "obesity", "high", exp, trend=trend, sparkline=sparkline)

    vitamin_d = raw.get("vitamin_d")
    if vitamin_d is not None:
        if vitamin_d < 20:
            recommendations.add("Discuss supplementation with clinician")
            exp = _explanation(
                "Vitamin D deficiency is below 20 ng/mL.",
                "<20 ng/mL",
                "Low vitamin D can affect bone health and immunity; supplementation may help.",
            )
            add_signal("Vitamin D", vitamin_d, "deficient", "moderate", exp)
        elif 20 <= vitamin_d < 30:
            recommendations.add("Increase safe sunlight or dietary vitamin D")
            exp = _explanation(
                "Vitamin D insufficiency is 20-29 ng/mL.",
                "20-29 ng/mL",
                "Raising vitamin D can support bone and immune health.",
            )
            add_signal("Vitamin D", vitamin_d, "insufficient", "moderate", exp)
        else:
            exp = _explanation(
                "Vitamin D of 30 ng/mL or higher is generally adequate.",
                ">=30 ng/mL",
                "Adequate vitamin D supports bone and immune function.",
            )
            add_signal("Vitamin D", vitamin_d, "adequate", "low", exp)

    vitamin_b12 = raw.get("vitamin_b12")
    if vitamin_b12 is not None:
        if vitamin_b12 < 200:
            recommendations.add("Assess B12 intake or absorption with clinician")
            exp = _explanation(
                "Vitamin B12 deficiency is below 200 pg/mL.",
                "<200 pg/mL",
                "Very low B12 can cause anemia and neurologic symptoms.",
            )
            add_signal("Vitamin B12", vitamin_b12, "deficient", "moderate", exp)
        elif 200 <= vitamin_b12 < 300:
            recommendations.add("Increase B12 sources and recheck")
            exp = _explanation(
                "Borderline low B12 is 200-299 pg/mL.",
                "200-299 pg/mL",
                "Borderline B12 can precede deficiency; monitoring is helpful.",
            )
            add_signal("Vitamin B12", vitamin_b12, "borderline_low", "moderate", exp)
        else:
            exp = _explanation(
                "Vitamin B12 of 300 pg/mL or higher is generally adequate.",
                ">=300 pg/mL",
                "Adequate B12 supports red blood cells and nerve health.",
            )
            add_signal("Vitamin B12", vitamin_b12, "adequate", "low", exp)

    ferritin = raw.get("ferritin")
    if ferritin is not None:
        if ferritin < 30:
            risks.add("iron_deficiency_risk")
            recommendations.add("Check iron intake and discuss with clinician")
            exp = _explanation(
                "Ferritin below 30 ng/mL can indicate low iron stores.",
                "<30 ng/mL",
                "Low ferritin may reflect iron deficiency, affecting energy and hair/skin.",
            )
            add_signal("Ferritin", ferritin, "low", "moderate", exp)
        elif ferritin > 400:
            doctor_flags.add("High ferritin - consider clinical evaluation")
            exp = _explanation(
                "Ferritin above 400 ng/mL is higher than typical reference ranges.",
                ">400 ng/mL",
                "High ferritin can indicate inflammation or iron overload and needs review.",
            )
            add_signal("Ferritin", ferritin, "high", "moderate", exp)
        else:
            exp = _explanation(
                "Ferritin between 30 and 400 ng/mL is within common reference ranges.",
                "30-400 ng/mL",
                "Ferritin in range suggests adequate iron stores.",
            )
            add_signal("Ferritin", ferritin, "normal", "low", exp)

    # --- Reproductive health ---
    cycle_length = raw.get("cycle_length_days")
    periods_missed = raw.get("periods_missed")
    cycle_irregular = raw.get("cycle_irregular")
    if cycle_length is not None:
        if cycle_length < 21:
            recommendations.add("Track cycles; consider clinician review")
            exp = _explanation(
                "Very short cycles are under 21 days.",
                "<21 days",
                "Short cycles can be normal for some but may reflect hormonal shifts.",
            )
            add_signal("Menstrual Cycle", cycle_length, "very_short_cycle", "moderate", exp)
        elif 21 <= cycle_length <= 35:
            exp = _explanation(
                "Regular cycle range is typically 21-35 days.",
                "21-35 days",
                "Cycles in this range are common for many menstruating people.",
            )
            add_signal("Menstrual Cycle", cycle_length, "regular_cycle_range", "low", exp)
        elif cycle_length > 35:
            recommendations.add("Irregular or long cycles - monitor and consult if persistent")
            exp = _explanation(
                "Long cycles are over 35 days.",
                ">35 days",
                "Long cycles can be normal for some but may warrant review if persistent.",
            )
            add_signal("Menstrual Cycle", cycle_length, "long_cycle", "moderate", exp)
    if periods_missed is not None and periods_missed >= 2:
        doctor_flags.add("Multiple missed cycles - consider medical evaluation")
        exp = _explanation(
            "Missing two or more cycles in a row should be evaluated.",
            ">=2 missed cycles",
            "Missed cycles can have many causes including pregnancy or hormonal changes.",
        )
        add_signal("Periods Missed", periods_missed, "missed_cycles", "moderate", exp)
    if cycle_irregular:
        recommendations.add("Track cycles and discuss patterns with clinician")
        exp = _explanation(
            "Irregular cycles vary significantly month to month.",
            "Irregular pattern",
            "Cycle irregularity can stem from stress, weight changes, or medical causes.",
        )
        add_signal("Cycle Regularity", "irregular", "irregular_cycles", "moderate", exp)

    # --- Mental / lifestyle ---
    stress_level = raw.get("stress_level")
    if stress_level is not None:
        if stress_level > 7:
            recommendations.add("Short daily stress-reduction practice")
            exp = _explanation(
                "High self-reported stress when above 7/10.",
                ">7/10",
                "High stress can affect sleep, blood pressure, and glucose control.",
            )
            add_signal("Stress", stress_level, "high_stress", "moderate", exp)
        elif 5 <= stress_level <= 7:
            exp = _explanation(
                "Moderate stress self-rating between 5 and 7/10.",
                "5-7/10",
                "Sustained moderate stress can accumulate; coping strategies help.",
            )
            add_signal("Stress", stress_level, "moderate_stress", "moderate", exp)
        else:
            exp = _explanation(
                "Manageable stress when reported under 5/10.",
                "<5/10",
                "Lower stress reports suggest current coping is effective.",
            )
            add_signal("Stress", stress_level, "manageable_stress", "low", exp)

    mood_variability = raw.get("mood_variability")
    if mood_variability is not None:
        if mood_variability > 7:
            recommendations.add("Keep a brief mood log and seek support if worsening")
            exp = _explanation(
                "High mood variability when swings are above 7/10.",
                ">7/10 variability",
                "Large mood swings can affect functioning; tracking helps spot patterns.",
            )
            add_signal("Mood Variability", mood_variability, "high_variability", "moderate", exp)
        elif 4 <= mood_variability <= 7:
            exp = _explanation(
                "Some mood variability when swings are 4-7/10.",
                "4-7/10 variability",
                "Moderate swings can be normal but worth observing over time.",
            )
            add_signal("Mood Variability", mood_variability, "some_variability", "context", exp)
        else:
            exp = _explanation(
                "Stable mood when variability is under 4/10.",
                "<4/10 variability",
                "Stable moods suggest current routines are supporting mental health.",
            )
            add_signal("Mood Variability", mood_variability, "stable", "low", exp)

    return {
        "signals": signals,
        "risks": sorted(risks),
        "recommendations": sorted(recommendations),
        "doctor_flags": sorted(doctor_flags),
    }
