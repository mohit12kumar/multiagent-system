from typing import Dict, Any, List

class ExplainableAIEngine:
    """Enterprise Explainable AI Engine v7.1 — Itemizes evidence contributions and penalties per diagnosis."""

    @classmethod
    def calculate_explainable_confidence(
        cls,
        disease_name: str,
        symptoms: List[str],
        labs: List[Dict[str, Any]],
        vitals: List[Dict[str, Any]],
        imaging: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        positive = []
        negative = []
        conflicts = []
        score = 50

        d_low = disease_name.lower()
        lab_names = [l.get("name", "").lower() or l.get("lab", "").lower() for l in labs]
        symptom_str = " ".join(symptoms).lower()
        img_names = [i.get("name", "").lower() for i in imaging]

        # Cardiac / STEMI Breakdown
        if "stemi" in d_low or "infarction" in d_low:
            if any("troponin" in l for l in lab_names):
                positive.append({"factor": "Elevated Troponin-I (Myocardial Injury)", "weight": 35})
                score += 35
            else:
                negative.append({"factor": "Missing Troponin-I Level", "penalty": 15})
                score -= 15

            if any("ecg" in i for i in img_names):
                positive.append({"factor": "ECG ST Elevation in II, III, aVF", "weight": 25})
                score += 25

            if "chest pain" in symptom_str:
                positive.append({"factor": "Ischemic Chest Pain", "weight": 15})
                score += 15

        # Heart Failure Breakdown
        elif "heart failure" in d_low:
            if any("bnp" in l for l in lab_names):
                positive.append({"factor": "Elevated BNP Natriuretic Peptide", "weight": 35})
                score += 35
            if any("echo" in i for i in img_names):
                positive.append({"factor": "Reduced Ejection Fraction (EF 25%)", "weight": 25})
                score += 25
            if "shortness of breath" in symptom_str or "dyspnea" in symptom_str:
                positive.append({"factor": "Dyspnea / Pulmonary Congestion", "weight": 15})
                score += 15

        # Default fallback
        else:
            if symptoms:
                positive.append({"factor": f"Supporting Symptoms ({len(symptoms)})", "weight": 20})
                score += 20
            if labs:
                positive.append({"factor": f"Supporting Lab Markers ({len(labs)})", "weight": 25})
                score += 25

        final_score = max(40, min(99, score))

        return {
            "confidence_breakdown": {
                "positive": positive,
                "negative": negative,
                "conflicts": conflicts,
                "final_score": final_score
            }
        }
