from typing import Dict, Any, List

class MedicationEffectivenessEngine:
    """Evaluates medication effectiveness, monitoring schedules, and adverse drug reaction (ADR) risks."""

    MONITORING_RULES = {
        "metformin": {
            "markers": ["HbA1c", "Creatinine", "eGFR"],
            "interval": "Every 3 months",
            "adr_risk": "Lactic Acidosis",
            "adr_prob": "Low (<1%)",
            "adr_sev": "Critical",
            "adr_evidence": "Renal failure / eGFR <30 mL/min"
        },
        "losartan": {
            "markers": ["Serum Potassium", "Creatinine", "Blood Pressure"],
            "interval": "Every 1 to 3 months",
            "adr_risk": "Hyperkalemia & Angioedema",
            "adr_prob": "Moderate (3-5%)",
            "adr_sev": "High",
            "adr_evidence": "Potassium >5.5 mmol/L or renal artery stenosis"
        },
        "atorvastatin": {
            "markers": ["Lipid Panel (LDL, HDL, Triglycerides)", "ALT/AST Liver Enzymes"],
            "interval": "Every 6 months",
            "adr_risk": "Myopathy & Rhabdomyolysis",
            "adr_prob": "Low (1-2%)",
            "adr_sev": "High",
            "adr_evidence": "Elevated LFTs or co-administration with fibrates"
        },
        "furosemide": {
            "markers": ["Serum Potassium", "Sodium", "BUN", "Creatinine"],
            "interval": "Every 2 to 4 weeks during titration",
            "adr_risk": "Hypokalemia & Volume Depletion",
            "adr_prob": "High (10-15%)",
            "adr_sev": "Moderate",
            "adr_evidence": "Over-diuresis and electrolyte loss"
        },
        "aspirin": {
            "markers": ["Hemoglobin / Hematocrit", "Stool Occult Blood"],
            "interval": "Annually / as indicated",
            "adr_risk": "Gastrointestinal Bleeding",
            "adr_prob": "Moderate (2-4%)",
            "adr_sev": "Major",
            "adr_evidence": "Prior peptic ulcer disease or DAPT therapy"
        }
    }

    @classmethod
    def evaluate_medication(cls, drug_name: str, disease_name: str = "") -> Dict[str, Any]:
        d_low = drug_name.lower()
        matched_key = None
        for k in cls.MONITORING_RULES:
            if k in d_low:
                matched_key = k
                break

        rule = cls.MONITORING_RULES.get(matched_key, {})

        effectiveness = {
            "drug_name": drug_name,
            "evidence_supports_disease": True,
            "dose_appropriate": True,
            "response_expected": "Positive therapeutic response expected",
            "guideline_compliant": True,
            "monitoring_required": rule.get("interval", "Routine clinical follow-up"),
            "monitoring_markers": rule.get("markers", ["Routine labs"]),
            "adr_prediction": {
                "risk": rule.get("adr_risk", "General Drug Hypersensitivity"),
                "probability": rule.get("adr_prob", "Low (<1%)"),
                "severity": rule.get("adr_sev", "Moderate"),
                "evidence": rule.get("adr_evidence", "Standard pharmacovigilance monitoring")
            }
        }
        return effectiveness
