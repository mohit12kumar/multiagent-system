from typing import Dict, Any, List

class EvidenceConfidenceEngine:
    """Calculates weighted explainable evidence confidence scores and generates 'Detected Because' checklists."""

    @classmethod
    def calculate_disease_confidence(
        cls,
        disease_name: str,
        symptoms: List[str],
        medication_present: bool,
        vitals_present: bool,
        labs_present: bool,
        assessment_present: bool = True,
        history_present: bool = False
    ) -> Dict[str, Any]:
        """
        Dynamic weighted evidence breakdown:
        - Assessment: 35%
        - Medication: 20%
        - Symptoms: 20%
        - Labs: 15%
        - Vitals: 5%
        - History: 5%
        Returns score bounded between 50% - 99%
        """
        w_assess  = 35.0 if assessment_present else 15.0
        w_meds    = 20.0 if medication_present else 0.0
        w_syms    = 20.0 if len(symptoms) > 0 else 0.0
        w_labs    = 15.0 if labs_present else 0.0
        w_vitals  = 5.0  if vitals_present else 0.0
        w_history = 5.0  if history_present else 0.0

        total_score = w_assess + w_meds + w_syms + w_labs + w_vitals + w_history
        normalized_confidence = min(0.99, max(0.50, round(total_score / 100.0, 2)))

        # Build Explainable "Detected Because" checklist
        detected_because = []
        if assessment_present:
            detected_because.append("Assessment / Diagnostic Impression")
        if history_present:
            detected_because.append("Documented Past Medical History")
        if len(symptoms) > 0:
            detected_because.append(f"Clinical Symptoms ({', '.join(symptoms[:3])})")
        if medication_present:
            detected_because.append("Targeted Medication Regimen")
        if labs_present:
            detected_because.append("Laboratory Findings")
        if vitals_present:
            detected_because.append("Vital Signs Interpretation")

        return {
            "overall_confidence": normalized_confidence,
            "overall_percentage": f"{int(normalized_confidence * 100)}%",
            "breakdown": {
                "assessment": f"{int(w_assess)}%",
                "medications": f"{int(w_meds)}%",
                "symptoms": f"{int(w_syms)}%",
                "labs": f"{int(w_labs)}%",
                "vitals": f"{int(w_vitals)}%",
                "history": f"{int(w_history)}%"
            },
            "detected_because": detected_because
        }
