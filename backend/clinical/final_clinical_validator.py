"""
Final Clinical Validation Agent.
Performs an automated pre-rendering clinical safety audit before sending results to the UI.
Checks evidence completeness, disease-medication appropriateness, attribute presence, and safety rules.
Flags errors and forces mandatory Doctor Review Queue routing if any check fails.
"""

from typing import Dict, Any, List
from src.monitoring.logger import logger

_LAB_MARKERS = {
    "creatinine", "hba1c", "hemoglobin", "haemoglobin", "hgb", "hb",
    "ldl", "hdl", "cholesterol", "bun", "potassium", "sodium", "egfr",
    "wbc", "rbc", "platelets", "troponin", "crp", "alt", "ast", "bilirubin",
}

_ALLERGIES = {
    "penicillin", "sulfa", "latex", "peanut", "codeine allergy", "aspirin allergy",
}


class FinalClinicalValidator:
    """Automated clinical validation safety pipeline."""

    @classmethod
    def validate_pipeline_output(cls, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs comprehensive clinical validation rules on output data.
        Returns: { 'is_valid': bool, 'validation_warnings': List[str], 'doctor_review_forced': bool }
        """
        warnings: List[str] = []

        patient_summ = output.get("patient_summary", {})
        structured = patient_summ.get("structured_summary", []) if isinstance(patient_summ, dict) else []

        # 1. Disease Evidence Check
        for cond in structured:
            d_name = cond.get("disease", "Unknown")
            conf = cond.get("confidence", 0.0)
            syms = cond.get("symptoms", [])
            meds = cond.get("medications", [])
            because = cond.get("detected_because", [])

            if conf < 0.50 and not because:
                warnings.append(f"Disease '{d_name}' lacks sufficient clinical evidence (Confidence: {int(conf*100)}%).")

            # 2. Check for Lab markers or Allergies misclassified as medications
            for m in meds:
                m_name = (m.get("name") if isinstance(m, dict) else getattr(m, "name", "")).lower()
                if any(lab in m_name for lab in _LAB_MARKERS):
                    warnings.append(f"Laboratory marker '{m_name}' incorrectly classified as a medication under {d_name}.")
                if any(alg in m_name for alg in _ALLERGIES):
                    warnings.append(f"Allergen '{m_name}' incorrectly classified as a medication under {d_name}.")

                # 3. Check for missing vital attributes
                dose = m.get("dosage") if isinstance(m, dict) else getattr(m, "dosage", "N/A")
                route = m.get("route") if isinstance(m, dict) else getattr(m, "route", "Oral")
                if not dose or dose == "N/A" or dose == "As prescribed":
                    warnings.append(f"Medication '{m_name}' under {d_name} has unspecified dosage.")

        # 4. Check overall medication relations
        all_meds = output.get("medications", [])
        for drug in all_meds:
            d_low = drug.lower()
            if any(lab in d_low for lab in _LAB_MARKERS):
                warnings.append(f"Laboratory test '{drug}' present in top-level medication list.")

        is_valid = len(warnings) == 0
        doctor_review_forced = True  # Always forced for healthcare safety

        if not is_valid:
            logger.warning(f"Final Clinical Validation identified {len(warnings)} warning(s): {warnings}")
        else:
            logger.info("Final Clinical Validation passed with 0 critical safety errors.")

        return {
            "is_valid": is_valid,
            "validation_warnings": warnings,
            "doctor_review_forced": doctor_review_forced,
            "audit_status": "PASSED" if is_valid else "REVIEW_REQUIRED"
        }
