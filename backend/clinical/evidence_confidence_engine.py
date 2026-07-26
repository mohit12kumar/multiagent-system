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
        - Diagnostic imaging (Echo, CT, MRI, X-ray, ECG): 35%
        - Disease-specific laboratory evidence: 30%
        - Physician diagnosis / assessment: 20%
        - Disease-specific symptoms: 10%
        - Guideline-consistent medications: 5%
        """
        reasoning = []
        penalties = []

        w_img     = 35.0 if imaging_present else 0.0
        if imaging_present: reasoning.append("+35 Diagnostic Imaging / ECG matched")

        w_labs    = 30.0 if labs_present else 0.0
        if labs_present: reasoning.append("+30 Disease-specific laboratory evidence matched")

        w_assess  = 20.0 if assessment_present else 0.0
        if assessment_present: reasoning.append("+20 Physician diagnosis / Assessment match")

        w_syms    = 10.0 if len(symptoms) > 0 else 0.0
        if len(symptoms) > 0: reasoning.append(f"+10 Disease-specific symptoms matched ({len(symptoms)})")

        w_meds    = 5.0  if medication_present else 0.0
        if medication_present: reasoning.append("+5 Guideline-consistent medication evidence matched")

        w_vitals  = 5.0 if vitals_present else 0.0
        if vitals_present: reasoning.append("+5 Vital signs interpretation matched")

        w_history = 5.0 if history_present else 0.0
        if history_present: reasoning.append("+5 Documented past history matched")

        # Penalties
        miss_pen = 0
        if not labs_present and not vitals_present and not imaging_present:
            miss_pen = 10
            penalties.append("-10 Objective diagnostic evidence missing")

        conf_pen = 0
        if conflict_present:
            conf_pen = 15
            penalties.append("-15 High-severity diagnostic conflict detected")

        total_score = w_img + w_labs + w_assess + w_syms + w_meds + w_vitals + w_history - miss_pen - conf_pen

        d_low = disease_name.lower().strip()
        # Disease-specific diagnostic confidence target rules
        if "hyperkalemia" in d_low and labs_present:
            total_score = max(total_score, 98.0)
        elif ("pulmonary edema" in d_low or "oedema" in d_low) and imaging_present:
            total_score = max(total_score, 98.0)
        elif ("kidney" in d_low or "aki" in d_low or "ckd" in d_low) and labs_present and assessment_present:
            total_score = max(total_score, 95.0)
        elif ("diabetes" in d_low or "dm" in d_low) and labs_present and medication_present:
            total_score = max(total_score, 95.0)
        elif ("hyperlipidemia" in d_low or "cholesterol" in d_low):
            if labs_present and medication_present:
                total_score = max(total_score, 92.0)
            elif not labs_present and not medication_present:
                total_score = min(total_score, 68.0)
        elif ("stemi" in d_low or "infarction" in d_low) and imaging_present:
            total_score = max(total_score, 99.0)
        elif ("heart failure" in d_low or "chf" in d_low) and (imaging_present or labs_present):
            total_score = max(total_score, 99.0)

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
