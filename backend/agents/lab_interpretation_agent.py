"""
LabInterpretationAgent -- Interprets laboratory values AND vital signs.

Each result includes:
  - lab / vital name
  - measured value with units
  - reference range
  - interpretation text
  - arrow indicator (up/down/normal)
  - supporting disease (the condition the abnormal value supports)
  - severity (Normal / Elevated / Critically Elevated / etc.)
"""

import re
from typing import Dict, Any, List, Optional


class LabInterpretationAgent:
    """Parses and interprets laboratory values and vital signs from clinical text."""

    # Each lab rule: (keyword, low, high, unit, low_msg, high_msg, low_severity, high_severity, low_disease, high_disease)
    LAB_RULES = [
        ("hba1c",      4.0,   5.6,  "%",          "Normal",             "Poor Glycemic Control",          "Normal", "Critically Elevated", None,                          "Type 2 Diabetes Mellitus"),
        ("blood glucose",70.0,140.0, "mg/dL",      "Hypoglycemia",       "Hyperglycemia / Poor Glycemic Control","Low", "Elevated",            "Hypoglycemia",                "Type 2 Diabetes Mellitus"),
        ("glucose",    70.0,  140.0,"mg/dL",      "Hypoglycemia",       "Hyperglycemia / Poor Glycemic Control","Low", "Elevated",            "Hypoglycemia",                "Type 2 Diabetes Mellitus"),
        ("creatinine", 0.6,   1.2,  "mg/dL",      "Normal",             "Renal Impairment",               "Normal", "Elevated",            None,                          "Chronic Kidney Disease"),
        ("egfr",       60.0,  150.0,"mL/min",     "Renal Impairment",   "Normal",                         "Low",    "Normal",              "Chronic Kidney Disease",      None),
        ("potassium",  3.5,   5.0,  "mmol/L",     "Hypokalemia",        "Hyperkalemia",                   "Low",    "Critically Elevated", "Hypokalemia",                 "Hyperkalemia / CKD"),
        ("sodium",     135.0, 145.0,"mmol/L",     "Hyponatremia",       "Hypernatremia",                  "Low",    "Elevated",            "Hyponatremia",                "Hypernatremia"),
        ("ldl",        0.0,   100.0,"mg/dL",      "Normal",             "Hyperlipidemia",                 "Normal", "Elevated",            None,                          "Hyperlipidemia"),
        ("hdl",        40.0,  999.0,"mg/dL",      "Low HDL (Risk Factor)","Normal",                       "Low",    "Normal",              "Hyperlipidemia / CVD Risk",   None),
        ("wbc",        4.5,   11.0, "x10^3/uL",   "Leukopenia",         "Leukocytosis / Infection",       "Low",    "Elevated",            "Immunosuppression",           "Community Acquired Pneumonia"),
        ("crp",        0.0,   3.0,  "mg/L",       "Normal",             "Inflammation / Infection",       "Normal", "Elevated",            None,                          "Community Acquired Pneumonia"),
        ("bun",        7.0,   20.0, "mg/dL",      "Normal",             "Renal Impairment / Uremia",      "Normal", "Elevated",            None,                          "Chronic Kidney Disease"),
        ("hemoglobin", 12.0,  17.0, "g/dL",       "Anaemia",            "Polycythaemia",                  "Low",    "Elevated",            "Anemia",                      None),
        ("haemoglobin",12.0,  17.0, "g/dL",       "Anaemia",            "Polycythaemia",                  "Low",    "Elevated",            "Anemia",                      None),
        ("troponin",   0.0,   0.04, "ng/mL",      "Normal",             "Myocardial Injury / ACS",        "Normal", "Critically Elevated", None,                          "Acute Inferior STEMI / Acute Myocardial Infarction"),
        ("troponin-i", 0.0,   0.04, "ng/mL",      "Normal",             "Myocardial Injury / ACS",        "Normal", "Critically Elevated", None,                          "Acute Inferior STEMI / Acute Myocardial Infarction"),
        ("platelets",  150.0, 400.0,"x10^3/uL",   "Thrombocytopenia",   "Thrombocytosis",                 "Low",    "Elevated",            "Thrombocytopenia",            None),
        ("alt",        7.0,   56.0, "U/L",         "Normal",             "Hepatic Injury",                 "Normal", "Elevated",            None,                          "Hepatic Disease"),
        ("ast",        10.0,  40.0, "U/L",         "Normal",             "Hepatic / Cardiac Injury",       "Normal", "Elevated",            None,                          "Hepatic Disease"),
        ("bnp",        0.0,   100.0,"pg/mL",       "Normal",             "Elevated Natriuretic Peptide",   "Normal", "Critically Elevated", None,                          "Heart Failure"),
        ("lactate",    0.0,   2.0,  "mmol/L",      "Normal",             "Hyperlactatemia / Sepsis Risk",  "Normal", "Critically Elevated", None,                          "Sepsis / Hypoperfusion"),
        ("d-dimer",    0.0,   500.0,"ng/mL",       "Normal",             "Elevated D-Dimer",              "Normal", "Elevated",            None,                          "Thromboembolism"),
    ]

    # Vital sign rules: (keyword_pattern, unit, severity_thresholds)
    # Thresholds: list of (max_value, label, severity, disease)
    VITAL_RULES = [
        {
            "name": "Blood Pressure",
            "pattern": r'(?:bp|blood\s*pressure)\s*[:\-]?\s*(\d{2,3})\s*/\s*(\d{2,3})',
            "unit": "mmHg",
            "type": "bp",
            "thresholds": [
                (120, 90, "Normal", "Normal", None),
                (130, 80, "Elevated", "Elevated", "Hypertension"),
                (140, 90, "Stage 1 Hypertension", "Elevated", "Hypertension"),
                (180, 120, "Stage 2 Hypertension", "Critically Elevated", "Hypertension"),
                (999, 999, "Hypertensive Crisis", "Critical", "Hypertension"),
            ]
        },
        {
            "name": "Heart Rate",
            "pattern": r'(?:hr|heart\s*rate|pulse)\s*[:\-]?\s*(\d{2,3})\s*(?:bpm|\/min)?',
            "unit": "bpm",
            "type": "single",
            "low": 60, "high": 100,
            "low_msg": "Bradycardia", "high_msg": "Tachycardia",
            "low_disease": "Cardiac Conduction Issue", "high_disease": "Atrial Fibrillation / Infection",
        },
        {
            "name": "Respiratory Rate",
            "pattern": r'(?:rr|respiratory\s*rate)\s*[:\-]?\s*(\d{1,2})\s*(?:\/min|breaths)?',
            "unit": "/min",
            "type": "single",
            "low": 12, "high": 20,
            "low_msg": "Bradypnea", "high_msg": "Tachypnea / Respiratory Distress",
            "low_disease": None, "high_disease": "COPD / Community Acquired Pneumonia",
        },
        {
            "name": "Temperature",
            "pattern": r'(?:temp(?:erature)?)\s*[:\-]?\s*(\d{2,3}(?:\.\d)?)\s*(?:F|C|degF|degC)?',
            "unit": "F",
            "type": "single",
            "low": 97.0, "high": 99.5,
            "low_msg": "Hypothermia", "high_msg": "Fever",
            "low_disease": None, "high_disease": "Community Acquired Pneumonia / Infection",
        },
        {
            "name": "SpO2",
            "pattern": r'(?:spo2|o2\s*sat(?:uration)?|oxygen\s*sat(?:uration)?)\s*[:\-]?\s*(\d{2,3})\s*%?',
            "unit": "%",
            "type": "single",
            "low": 95.0, "high": 100.0,
            "low_msg": "Hypoxemia", "high_msg": "Normal",
            "low_disease": "COPD / Community Acquired Pneumonia", "high_disease": None,
        },
    ]

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def interpret_labs(self, text: str) -> List[Dict[str, Any]]:
        """Parse and interpret laboratory values from clinical text."""
        interpretations = []
        text_lower = text.lower()
        seen: set = set()

        CANONICAL_LAB_MAP = {
            "glucose": "Blood Glucose",
            "blood glucose": "Blood Glucose",
            "serum glucose": "Blood Glucose",
            "random glucose": "Blood Glucose",
            "fasting glucose": "Blood Glucose",
        }

        display_names = {
            "hba1c": "HbA1c", "egfr": "eGFR", "wbc": "WBC",
            "crp": "CRP", "bun": "BUN", "ldl": "LDL", "hdl": "HDL",
            "alt": "ALT", "ast": "AST", "bnp": "BNP",
            "blood glucose": "Blood Glucose", "glucose": "Blood Glucose"
        }

        for rule in self.LAB_RULES:
            kw, low, high, unit, low_msg, high_msg, low_sev, high_sev, low_dis, high_dis = rule
            pattern = re.compile(rf"\b{re.escape(kw)}\b[\s\:\-]*([\d]+(?:\.\d+)?)", re.IGNORECASE)
            for m in pattern.finditer(text_lower):
                val_str = m.group(1)
                try:
                    val = float(val_str)
                    lab_name = CANONICAL_LAB_MAP.get(kw.lower(), display_names.get(kw.lower(), kw.title()))
                    dedup_key = f"{lab_name.lower()}_{val_str}"
                    if dedup_key in seen:
                        continue
                    seen.add(dedup_key)

                    if val < low:
                        interp, arrow, severity, disease = low_msg, "↓", low_sev, low_dis
                    elif val > high:
                        interp, arrow, severity, disease = high_msg, "↑", high_sev, high_dis
                    else:
                        interp, arrow, severity, disease = "Normal", "→", "Normal", None

                    # Special CKD staging for eGFR
                    if kw == "egfr" and val < 60:
                        if val < 15:
                            interp, severity, disease = "CKD Stage V (Kidney Failure)", "Critical", "Chronic Kidney Disease"
                        elif val < 30:
                            interp, severity, disease = "CKD Stage IV (Severe)", "Critical", "Chronic Kidney Disease"
                        elif val < 45:
                            interp, severity, disease = "CKD Stage IIIb (Moderate)", "Critically Elevated", "Chronic Kidney Disease"
                        elif val < 60:
                            interp, severity, disease = "CKD Stage IIIa (Mild-Moderate)", "Elevated", "Chronic Kidney Disease"
                        arrow = "↓"

                    interpretations.append({
                        "lab": lab_name,
                        "value": val_str,
                        "unit": unit,
                        "reference_range": f"{low}-{high} {unit}",
                        "arrow": arrow,
                        "interpretation": interp,
                        "severity": severity,
                        "supporting_disease": disease
                    })
                except ValueError:
                    pass

        return interpretations

    @classmethod
    def check_ckd_stage_mismatch(cls, text: str, egfr_val: Optional[float]) -> Optional[Dict[str, str]]:
        """Checks if reported CKD stage in note mismatches calculated stage from eGFR."""
        if egfr_val is None:
            return None
        
        calc_stage = "Stage I"
        if egfr_val < 15:
            calc_stage = "Stage V"
        elif egfr_val < 30:
            calc_stage = "Stage IV"
        elif egfr_val < 45:
            calc_stage = "Stage IIIb"
        elif egfr_val < 60:
            calc_stage = "Stage IIIa"
        elif egfr_val < 90:
            calc_stage = "Stage II"

        import re
        m = re.search(r'(?:ckd|chronic\s+kidney\s+disease)\s*(?:stage)?\s*([i|v|1-5]+)', text.lower())
        if m:
            reported_raw = m.group(1).upper()
            if "III" in reported_raw or "3" in reported_raw:
                rep_stage = "Stage III"
                if "IV" in calc_stage or "V" in calc_stage:
                    return {
                        "warning": f"Possible Stage Mismatch (Reported: {rep_stage}, Calculated: {calc_stage} from eGFR {egfr_val})",
                        "reported_stage": rep_stage,
                        "calculated_stage": calc_stage
                    }
        return None

    def interpret_vitals(self, text: str) -> List[Dict[str, Any]]:
        """Parse and interpret vital signs from clinical text."""
        results = []
        seen_vitals: set = set()

        for rule in self.VITAL_RULES:
            pat = re.compile(rule["pattern"], re.IGNORECASE)
            m = pat.search(text)
            if not m:
                continue

            name = rule["name"]
            if name in seen_vitals:
                continue
            seen_vitals.add(name)

            if rule["type"] == "bp":
                try:
                    systolic = int(m.group(1))
                    diastolic = int(m.group(2))
                    val_str = f"{systolic}/{diastolic}"
                    if systolic < 90 or diastolic < 60:
                        label = "Hypotension"
                        severity = "Low"
                        disease = "Hypotension / Hypoperfusion"
                        arrow = "↓"
                    else:
                        label, severity, disease = "Normal", "Normal", None
                        for sys_th, dia_th, lbl, sev, dis in rule["thresholds"]:
                            if systolic >= sys_th or diastolic >= dia_th:
                                label, severity, disease = lbl, sev, dis
                        arrow = "↑" if severity not in ("Normal", None) else "→"
                    results.append({
                        "vital": name,
                        "value": f"{val_str} {rule['unit']}",
                        "reference": "90/60 - 120/80 mmHg",
                        "interpretation": label,
                        "arrow": arrow,
                        "severity": severity,
                        "supporting_disease": disease,
                    })
                except Exception:
                    continue
            else:
                try:
                    val = float(m.group(1))
                    unit_str = rule["unit"]
                    low  = rule["low"]
                    high = rule["high"]

                    if name == "Temperature":
                        is_celsius = bool(re.search(r'\b' + str(val) + r'\s*°?\s*c\b', text, re.IGNORECASE)) or val < 45.0
                        if is_celsius:
                            unit_str = "°C"
                            low, high = 35.0, 37.5
                            if val > 37.5:
                                interp, arrow, disease = "Fever (Hyperthermia)", "↑", rule["high_disease"]
                                severity = "Critically Elevated"
                            elif val < 35.0:
                                interp, arrow, disease = "Hypothermia", "↓", rule["low_disease"]
                                severity = "Low"
                            else:
                                interp, arrow, disease = "Normal", "→", None
                                severity = "Normal"
                        else:
                            unit_str = "°F"
                            low, high = 95.0, 99.5
                            if val > 99.5:
                                interp, arrow, disease = "Fever (Hyperthermia)", "↑", rule["high_disease"]
                                severity = "Critically Elevated"
                            elif val < 95.0:
                                interp, arrow, disease = "Hypothermia", "↓", rule["low_disease"]
                                severity = "Low"
                            else:
                                interp, arrow, disease = "Normal", "→", None
                                severity = "Normal"
                    else:
                        if val < low:
                            interp, arrow, disease = rule["low_msg"],  "↓", rule["low_disease"]
                            severity = "Low"
                        elif val > high:
                            interp, arrow, disease = rule["high_msg"], "↑", rule["high_disease"]
                            severity = "Elevated"
                        else:
                            interp, arrow, disease = "Normal", "→", None
                            severity = "Normal"

                    results.append({
                        "vital": name,
                        "value": f"{val} {unit_str}",
                        "reference": f"{low}–{high} {unit_str}",
                        "interpretation": interp,
                        "arrow": arrow,
                        "severity": severity,
                        "supporting_disease": disease,
                    })
                except Exception:
                    continue

        return results

    def interpret_imaging_diagnostics(self, text: str) -> List[Dict[str, Any]]:
        """Parse and interpret imaging, ECG, echocardiogram, and diagnostic measurements dynamically from clinical text."""
        findings = []
        text_low = text.lower()

        # Echocardiogram / Ejection Fraction
        m_ef = re.search(r'(?:echo|lvef|ef|ejection\s*fraction)\s*[:\-]?\s*(\d{1,2})%', text_low)
        if m_ef:
            val = int(m_ef.group(1))
            findings.append({
                "category": "Echo",
                "name": "Ejection Fraction (EF)",
                "value": f"{val}%",
                "status": "Low (<40%)" if val < 40 else "Normal",
                "supporting_disease": "Heart Failure"
            })

        # ECG Findings
        if "st elevation" in text_low or "st-elevation" in text_low or "stemi" in text_low:
            m_ecg = re.search(r'st\s*elevation\s*(?:in\s*)?([a-z0-9\s,\/]+)', text_low)
            lead_str = m_ecg.group(1).strip().upper() if m_ecg else "II, III, aVF"
            findings.append({
                "category": "ECG",
                "name": "ECG ST Elevation",
                "value": f"ST Elevation in {lead_str}",
                "status": "Critical",
                "supporting_disease": "Acute Inferior STEMI"
            })
        if "peaked t wave" in text_low or "peaked t-wave" in text_low:
            findings.append({
                "category": "ECG",
                "name": "ECG Peaked T Waves",
                "value": "Peaked T waves present",
                "status": "Critical",
                "supporting_disease": "Hyperkalemia"
            })

        # Chest X-Ray
        if "pulmonary edema" in text_low or "alveolar fluid" in text_low:
            findings.append({
                "category": "Imaging",
                "name": "Chest X-Ray",
                "value": "Pulmonary edema / alveolar fluid overload",
                "status": "High",
                "supporting_disease": "Heart Failure / Acute Pulmonary Edema"
            })
        if "infiltrate" in text_low or "consolidation" in text_low:
            m_cxr = re.search(r'([a-z\s]+(?:infiltrate|consolidation))', text_low)
            cxr_val = m_cxr.group(1).strip().title() if m_cxr else "Pulmonary Infiltrate / Consolidation"
            findings.append({
                "category": "Imaging",
                "name": "Chest X-Ray",
                "value": cxr_val,
                "status": "High",
                "supporting_disease": "Community Acquired Pneumonia"
            })

        # Urine Output
        m_uo = re.search(r'(?:urine\s*output|u\/o)\s*[:\-]?\s*(\d{2,4})\s*(?:ml|cc)?(?:\/day|\/24h)?', text_low)
        if m_uo:
            val_uo = int(m_uo.group(1))
            findings.append({
                "category": "Diagnostic",
                "name": "Urine Output",
                "value": f"{val_uo} mL/day",
                "status": "Oliguria (<500 mL/day)" if val_uo < 500 else "Normal",
                "supporting_disease": "Acute Kidney Injury"
            })

        # Smoking History
        m_pack = re.search(r'(\d{1,3})\s*pack[\s\-]*year', text_low)
        if m_pack:
            findings.append({
                "category": "History",
                "name": "Smoking History",
                "value": f"{m_pack.group(1)} pack-years",
                "status": "High Risk",
                "supporting_disease": "COPD"
            })

        return findings
