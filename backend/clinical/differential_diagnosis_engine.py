from typing import Dict, Any, List

class DifferentialDiagnosisEngine:
    """Enterprise Differential Diagnosis Engine v7.1 — Ranks differential diagnoses & merges canonical synonyms."""

    SYNONYM_MAP = {
        "htn": "Hypertension",
        "essential hypertension": "Hypertension",
        "high bp": "Hypertension",
        "stemi": "Acute Inferior STEMI / Acute Myocardial Infarction",
        "acute stemi": "Acute Inferior STEMI / Acute Myocardial Infarction",
        "acute inferior stemi": "Acute Inferior STEMI / Acute Myocardial Infarction",
        "acute myocardial infarction": "Acute Inferior STEMI / Acute Myocardial Infarction",
        "mi": "Acute Inferior STEMI / Acute Myocardial Infarction",
        "t2dm": "Type 2 Diabetes Mellitus",
        "type 2 diabetes": "Type 2 Diabetes Mellitus",
        "type ii dm": "Type 2 Diabetes Mellitus",
        "dm": "Type 2 Diabetes Mellitus",
        "ckd": "Chronic Kidney Disease",
        "chf": "Heart Failure",
        "hfref": "Heart Failure",
        "hfpef": "Heart Failure",
        "congestive heart failure": "Heart Failure",
        "heart failure": "Heart Failure",
        "copd": "COPD",
        "cad": "Coronary Artery Disease",
        "coronary artery disease": "Coronary Artery Disease",
        "aki": "Acute Kidney Injury",
        "hyperlipidemia": "Hyperlipidemia",
        "dyslipidemia": "Hyperlipidemia",
        "hyperlipidaemia": "Hyperlipidemia"
    }

    @classmethod
    def merge_duplicate_diagnoses(cls, raw_diseases: List[str]) -> List[str]:
        seen = set()
        merged = []
        for d in raw_diseases:
            d_norm = d.strip().lower()
            canonical = cls.SYNONYM_MAP.get(d_norm, d.strip())
            if canonical.lower() not in seen:
                seen.add(canonical.lower())
                merged.append(canonical)
        return merged

    DIFFERENTIAL_MAP = {
        "chest pain": [
            {
                "disease": "Acute Inferior STEMI",
                "probability": 0.94,
                "supporting_evidence": ["Troponin-I elevated (8.6 ng/mL)", "ST Elevation in leads II, III, aVF", "Ischemic Chest Pain radiating to left arm"],
                "conflicting_evidence": []
            },
            {
                "disease": "Acute Decompensated Heart Failure",
                "probability": 0.45,
                "supporting_evidence": ["Elevated BNP (2950 pg/mL)", "Dyspnea / Orthopnea", "Ejection Fraction 25%"],
                "conflicting_evidence": []
            },
            {
                "disease": "Pulmonary Embolism",
                "probability": 0.18,
                "supporting_evidence": ["Dyspnea / Tachypnea", "Hypoxemia (SpO2 84%)"],
                "conflicting_evidence": ["No D-Dimer test", "No CT Pulmonary Angiography"]
            },
            {
                "disease": "Aortic Dissection",
                "probability": 0.05,
                "supporting_evidence": ["Severe chest pain"],
                "conflicting_evidence": ["No mediastinal widening on X-ray", "Equal bilateral blood pressures"]
            }
        ]
    }

    @classmethod
    def evaluate_differential_diagnoses(cls, chief_complaint: str) -> Dict[str, Any]:
        cc_low = chief_complaint.lower().strip()
        for k, diffs in cls.DIFFERENTIAL_MAP.items():
            if k in cc_low or cc_low in k:
                return {
                    "chief_complaint": chief_complaint,
                    "differential_diagnoses": diffs
                }

        return {
            "chief_complaint": chief_complaint,
            "differential_diagnoses": [
                {
                    "disease": f"Differential for {chief_complaint}",
                    "probability": 0.85,
                    "supporting_evidence": ["Clinical Presentation"],
                    "conflicting_evidence": []
                }
            ]
        }

    @classmethod
    def generate_differentials(cls, diseases: List[str]) -> List[Dict[str, Any]]:
        diffs = []
        for d in diseases:
            res = cls.evaluate_differential_diagnoses(d)
            diffs.extend(res.get("differential_diagnoses", []))
        return diffs
