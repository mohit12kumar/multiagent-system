from typing import Dict, Any, List

class EvidenceConfidenceEngine:
    """Calculates weighted explainable evidence confidence scores, evidence ranking, and confidence explanations."""

    @classmethod
    def calculate_disease_confidence(
        cls,
        disease_name: str,
        symptoms: List[str],
        medication_present: bool,
        vitals_present: bool,
        labs_present: bool,
        assessment_present: bool = True,
        history_present: bool = False,
        imaging_present: bool = False,
        conflict_present: bool = False
    ) -> Dict[str, Any]:
        """
        Dynamic weighted evidence breakdown:
        - Assessment / Diagnostic Impression: 35%
        - Labs Evidence: 25%
        - Medication Evidence: 20%
        - Symptoms Evidence: 20%
        - Imaging Evidence: 15%
        - Vitals Evidence: 5%
        - History: 5%
        """
        reasoning = []
        penalties = []

        w_assess  = 35.0 if assessment_present else 15.0
        if assessment_present: reasoning.append("+35 Diagnostic Assessment match")

        w_labs    = 25.0 if labs_present else 0.0
        if labs_present: reasoning.append("+25 Laboratory evidence matched")

        w_meds    = 20.0 if medication_present else 0.0
        if medication_present: reasoning.append("+20 Targeted medication evidence matched")

        w_syms    = 20.0 if len(symptoms) > 0 else 0.0
        if len(symptoms) > 0: reasoning.append(f"+20 Clinical symptoms matched ({len(symptoms)})")

        w_img     = 15.0 if imaging_present else 0.0
        if imaging_present: reasoning.append("+15 Imaging / Diagnostic ECG matched")

        w_vitals  = 5.0 if vitals_present else 0.0
        if vitals_present: reasoning.append("+5 Vital signs interpretation matched")

        w_history = 5.0 if history_present else 0.0
        if history_present: reasoning.append("+5 Documented past history matched")

        # Penalties
        miss_pen = 0
        if not labs_present and not vitals_present:
            miss_pen = 5
            penalties.append("-5 Objective lab/vital evidence missing")

        conf_pen = 0
        if conflict_present:
            conf_pen = 15
            penalties.append("-15 High-severity diagnostic conflict detected")

        total_score = w_assess + w_labs + w_meds + w_syms + w_img + w_vitals + w_history - miss_pen - conf_pen
        raw_pct = min(99, max(40, int(total_score)))
        normalized_confidence = round(raw_pct / 100.0, 2)

        # Confidence Band Determination
        if raw_pct >= 95: band = "Confirmed"
        elif raw_pct >= 85: band = "High"
        elif raw_pct >= 70: band = "Moderate"
        else: band = "Needs Review"

        # Build Explainable "Detected Because" checklist
        detected_because = []
        if assessment_present: detected_because.append("✓ Assessment / Diagnostic Impression")
        if len(symptoms) > 0: detected_because.append(f"✓ Clinical Symptoms ({', '.join(symptoms[:3])})")
        if labs_present: detected_because.append("✓ Laboratory Findings")
        if vitals_present: detected_because.append("✓ Vital Signs Interpretation")
        if imaging_present: detected_because.append("✓ Diagnostic Imaging / ECG Findings")
        if medication_present: detected_because.append("✓ Targeted Medication Regimen")

        # Evidence Strength Weighting & Ranking Breakdown
        ranked_evidence = cls.rank_evidence(symptoms, labs_present, vitals_present, imaging_present, medication_present, history_present)

        return {
            "overall_confidence": normalized_confidence,
            "overall_percentage": f"{raw_pct}%",
            "score": raw_pct,
            "band": band,
            "reasoning": reasoning,
            "penalties": penalties if penalties else ["-0 Contradiction", "-0 Missing evidence"],
            "breakdown": {
                "assessment": f"{int(w_assess)}%",
                "medications": f"{int(w_meds)}%",
                "symptoms": f"{int(w_syms)}%",
                "labs": f"{int(w_labs)}%",
                "vitals": f"{int(w_vitals)}%",
                "history": f"{int(w_history)}%"
            },
            "detected_because": detected_because,
            "ranked_evidence": ranked_evidence,
            "confidence": {
                "score": raw_pct,
                "band": band,
                "reasoning": reasoning,
                "penalties": penalties if penalties else ["-0 Contradiction", "-0 Missing evidence"]
            }
        }

    @classmethod
    def rank_evidence(
        cls,
        symptoms: List[str],
        labs_present: bool,
        vitals_present: bool,
        imaging_present: bool,
        medication_present: bool,
        history_present: bool
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Ranks evidence into Primary, Secondary, Supporting, and Weak categories with strength weights."""
        primary = []
        secondary = []
        supporting = []
        weak = []

        if labs_present:
            primary.append({"item": "Objective Laboratory Markers", "weight": 100, "category": "Lab"})
        if imaging_present:
            primary.append({"item": "ECG / Imaging Findings", "weight": 95, "category": "Imaging"})

        if symptoms:
            for s in symptoms[:2]:
                secondary.append({"item": s, "weight": 40, "category": "Symptom"})

        if medication_present:
            supporting.append({"item": "Targeted Medication Prescription", "weight": 20, "category": "Medication"})
        if history_present:
            supporting.append({"item": "Documented Medical History", "weight": 15, "category": "History"})

        if not primary and secondary:
            primary.append({"item": secondary.pop(0)["item"], "weight": 60, "category": "Symptom"})

        if vitals_present:
            weak.append({"item": "Vital Signs Threshold", "weight": 10, "category": "Vital"})

        return {
            "primary": primary,
            "secondary": secondary,
            "supporting": supporting,
            "weak": weak
        }
