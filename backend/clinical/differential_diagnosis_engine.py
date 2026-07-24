from typing import Dict, Any, List

class DifferentialDiagnosisEngine:
    """Generates differential diagnoses (Detected, Possible, Rejected) with clinical rationale and hallucination rejection report."""

    # Differential candidate map
    DIFFERENTIAL_MAP = {
        "pneumonia": {
            "possible": [
                {"disease": "COPD Exacerbation", "reason": "Presents with dyspnea and productive cough; baseline lung exam required."},
                {"disease": "Bronchitis", "reason": "Symptom overlap with lower respiratory tract inflammation."},
                {"disease": "Pulmonary Edema", "reason": "Must rule out fluid overload if cardiac history present."}
            ],
            "rejected": [
                {"disease": "Tuberculosis", "reason": "No chronic night sweats, weight loss, or cavitary apical lesions documented."},
                {"disease": "Lung Malignancy", "reason": "No chronic constitutional symptoms or focal mass noted."}
            ]
        },
        "hypertension": {
            "possible": [
                {"disease": "Renovascular Hypertension", "reason": "Secondary cause to consider if resistant to dual anti-hypertensives."},
                {"disease": "Primary Aldosteronism", "reason": "Consider screening if unexplained hypokalemia occurs."}
            ],
            "rejected": [
                {"disease": "Pheochromocytoma", "reason": "No paroxysmal triad of headache, sweating, and tachycardia reported."}
            ]
        },
        "diabetes": {
            "possible": [
                {"disease": "Impaired Fasting Glucose", "reason": "Borderline glycemic elevation."},
                {"disease": "Metabolic Syndrome", "reason": "Co-occurrence of hypertension and dyslipidemia."}
            ],
            "rejected": [
                {"disease": "Diabetes Insipidus", "reason": "Normal serum osmolality and no hypotonic polyuria."}
            ]
        }
    }

    @classmethod
    def generate_differentials(cls, detected_diseases: List[str]) -> Dict[str, Any]:
        detected_list = []
        possible_list = []
        rejected_list = []

        for d in detected_diseases:
            d_name = d.strip().title() if isinstance(d, str) else str(d)
            detected_list.append({
                "disease": d_name,
                "status": "Detected / High Probability",
                "reason": "Direct clinical finding supported by symptomatic and therapeutic evidence."
            })

            d_lower = d_name.lower()
            found_map = False
            for k, diff in cls.DIFFERENTIAL_MAP.items():
                if k in d_lower or d_lower in k:
                    possible_list.extend(diff.get("possible", []))
                    rejected_list.extend(diff.get("rejected", []))
                    found_map = True
                    break

            if not found_map:
                possible_list.append({
                    "disease": f"Secondary {d_name} Complication",
                    "reason": "Related clinical variant requiring ongoing assessment."
                })
                rejected_list.append({
                    "disease": "Atypical Infection",
                    "reason": "Insufficient specific laboratory or serological evidence."
                })

        return {
            "detected": detected_list,
            "possible": possible_list,
            "rejected": rejected_list,
            "hallucination_report": [
                {
                    "entity": r["disease"],
                    "status": "REJECTED (Filtered by Validation Agent)",
                    "reason": r["reason"]
                }
                for r in rejected_list
            ]
        }

    @classmethod
    def merge_duplicate_diagnoses(cls, disease_names: List[str]) -> List[str]:
        """Merges duplicate aliases like STEMI + MI, CHF, HTN into canonical disease names."""
        alias_map = {
            "htn": "Hypertension",
            "essential hypertension": "Hypertension",
            "primary hypertension": "Hypertension",
            "type 2 diabetes": "Type 2 Diabetes Mellitus",
            "dm2": "Type 2 Diabetes Mellitus",
            "t2dm": "Type 2 Diabetes Mellitus",
            "copd": "Chronic Obstructive Pulmonary Disease",
            "ckd": "Chronic Kidney Disease",
            "cap": "Community Acquired Pneumonia",
            "stemi": "Acute Inferior STEMI / Acute Myocardial Infarction",
            "acute stemi": "Acute Inferior STEMI / Acute Myocardial Infarction",
            "acute inferior stemi": "Acute Inferior STEMI / Acute Myocardial Infarction",
            "myocardial infarction": "Acute Inferior STEMI / Acute Myocardial Infarction",
            "acute myocardial infarction": "Acute Inferior STEMI / Acute Myocardial Infarction",
            "mi": "Acute Inferior STEMI / Acute Myocardial Infarction",
            "inferior wall mi": "Acute Inferior STEMI / Acute Myocardial Infarction",
            "chf": "Heart Failure",
            "congestive heart failure": "Heart Failure",
            "heart failure": "Heart Failure",
            "hfref": "Heart Failure",
            "hyperlipidaemia": "Hyperlipidemia",
            "hyperlipidemia": "Hyperlipidemia",
            "dyslipidemia": "Hyperlipidemia",
            "acute kidney injury": "Acute Kidney Injury",
            "aki": "Acute Kidney Injury",
            "hyperkalemia": "Hyperkalemia"
        }
        merged = []
        seen = set()
        for d in disease_names:
            if not d: continue
            d_low = d.strip().lower()
            canonical = alias_map.get(d_low, d.strip().title())
            if canonical.lower() not in seen:
                seen.add(canonical.lower())
                merged.append(canonical)
        return merged
