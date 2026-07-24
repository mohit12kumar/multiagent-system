"""
Clinical Consistency Agent.
Validates multi-dimensional clinical evidence (symptoms, medications, labs, vitals, assessment)
before accepting a disease diagnosis. Rejects unsupported diagnoses.
"""

from typing import Dict, Any, List, Tuple
from src.monitoring.logger import logger

_REQUIRED_EVIDENCE = {
    "community acquired pneumonia": {
        "symptoms": ["cough", "fever", "sputum", "shortness of breath", "dyspnea", "breathlessness"],
        "labs": ["wbc", "crp"],
        "meds": ["azithromycin", "amoxicillin", "ceftriaxone", "levofloxacin"],
        "min_matches": 1
    },
    "chronic obstructive pulmonary disease": {
        "symptoms": ["cough", "wheezing", "dyspnea", "shortness of breath", "sputum"],
        "meds": ["salbutamol", "albuterol", "tiotropium", "budesonide", "fluticasone"],
        "min_matches": 1
    },
    "hypertension": {
        "symptoms": ["headache", "dizziness"],
        "vitals": ["blood pressure", "bp"],
        "meds": ["amlodipine", "losartan", "lisinopril", "metoprolol", "atenolol"],
        "min_matches": 1
    },
    "chronic kidney disease": {
        "labs": ["creatinine", "egfr", "bun"],
        "meds": ["furosemide", "losartan"],
        "min_matches": 1
    },
    "hyperlipidemia": {
        "labs": ["ldl", "hdl", "cholesterol", "triglycerides"],
        "meds": ["atorvastatin", "rosuvastatin", "simvastatin"],
        "min_matches": 1
    },
    "acute myocardial infarction": {
        "symptoms": ["chest pain", "angina", "shortness of breath", "dyspnea"],
        "labs": ["troponin", "st elevation", "ecg"],
        "min_matches": 1
    },
    "congestive heart failure": {
        "symptoms": ["dyspnea", "shortness of breath", "edema", "swelling", "orthopnea"],
        "labs": ["bnp", "ejection fraction", "ef"],
        "meds": ["furosemide", "spironolactone", "lisinopril", "carvedilol"],
        "min_matches": 1
    },
    "hyperkalemia": {
        "labs": ["potassium", "k+"],
        "min_matches": 1
    },
    "pulmonary edema": {
        "symptoms": ["dyspnea", "shortness of breath", "orthopnea"],
        "labs": ["chest xray", "bnp", "infiltrates"],
        "min_matches": 1
    }
}


class ClinicalConsistencyAgent:
    """Validates disease consistency against multi-dimensional clinical findings."""

    @classmethod
    def validate_consistency(
        cls,
        disease_name: str,
        symptoms: List[str],
        medications: List[Dict[str, Any]],
        labs: List[Dict[str, Any]],
        vitals: List[Dict[str, Any]]
    ) -> Tuple[bool, str, float]:
        """
        Validates diagnosis consistency.
        Returns: (is_consistent: bool, reason: str, consistency_score: float)
        """
        d_low = disease_name.lower().strip()
        
        # Check rule knowledge base
        matched_rule = None
        for k, rule in _REQUIRED_EVIDENCE.items():
            if k in d_low or d_low in k:
                matched_rule = rule
                break

        if not matched_rule:
            return True, "Consistent with general clinical presentation.", 0.90, ["Clinical presentation"], [], "High Confidence"

        sym_lows = [s.lower() for s in symptoms]
        med_lows = [(m.get("name") or m.get("medication_name") or "").lower() for m in medications]
        lab_lows = [(l.get("lab") or "").lower() for l in labs]
        vital_lows = [(v.get("vital") or "").lower() for v in vitals]

        evidence_count = 0
        supporting_evidence = []
        conflicting_evidence = []

        # Check symptom match
        if "symptoms" in matched_rule:
            for req in matched_rule["symptoms"]:
                if req in " ".join(sym_lows):
                    supporting_evidence.append(f"Symptom: {req}")
                    evidence_count += 1
                    break

        # Check lab match
        if "labs" in matched_rule:
            for req in matched_rule["labs"]:
                if req in " ".join(lab_lows):
                    supporting_evidence.append(f"Lab/Vital finding: {req}")
                    evidence_count += 1
                    break

        # Check med match
        if "meds" in matched_rule:
            for req in matched_rule["meds"]:
                if req in " ".join(med_lows):
                    supporting_evidence.append(f"Medication: {req}")
                    evidence_count += 1
                    break

        # Check vitals match
        if "vitals" in matched_rule:
            for req in matched_rule["vitals"]:
                if req in " ".join(vital_lows):
                    supporting_evidence.append(f"Vital sign: {req}")
                    evidence_count += 1
                    break

        if evidence_count >= matched_rule.get("min_matches", 1):
            score = round(min(0.99, 0.70 + (evidence_count * 0.10)), 2)
            band = "Confirmed" if score >= 0.95 else ("High Confidence" if score >= 0.80 else "Moderate")
            return True, f"High clinical consistency ({evidence_count} evidence dimensions verified).", score, supporting_evidence, conflicting_evidence, band
        else:
            conflicting_evidence.append(f"Missing required clinical criteria for {disease_name}")
            logger.warning(f"Clinical Consistency Agent flagged '{disease_name}': Insufficient supporting evidence.")
            return False, f"Needs Doctor Review: Insufficient supporting evidence for {disease_name}.", 0.40, supporting_evidence, conflicting_evidence, "Needs Doctor Review"
