from typing import Dict, Any, List

class ClinicalCompletenessEngine:
    """Enterprise Clinical Completeness Checklist Engine v7.1."""

    @classmethod
    def evaluate_completeness(
        cls,
        text: str,
        diseases: List[str],
        medications: List[Any],
        labs: List[Any],
        imaging: List[Any]
    ) -> Dict[str, Any]:

        t_low = text.lower()

        history_ok = "history" in t_low or "hpi" in t_low or "past medical history" in t_low
        exam_ok = "vital" in t_low or "physical exam" in t_low or "bp " in t_low or "heart rate" in t_low
        labs_ok = len(labs) >= 3
        imaging_ok = len(imaging) >= 1 or "ecg" in t_low or "x-ray" in t_low or "echo" in t_low
        meds_ok = len(medications) >= 1
        followup_ok = "follow" in t_low or "re-evaluate" in t_low or "discontinue" in t_low

        checklist = {
            "history": "✓" if history_ok else "✗",
            "examination": "✓" if exam_ok else "✗",
            "laboratories": "✓" if labs_ok else "✗",
            "imaging": "✓" if imaging_ok else "✗",
            "medications": "✓" if meds_ok else "✗",
            "follow_up": "✓" if followup_ok else "✗"
        }

        completed_count = sum(1 for v in checklist.values() if v == "✓")
        percentage = round((completed_count / len(checklist)) * 100)

        return {
            "clinical_completeness_checklist": checklist,
            "checklist_score": f"{percentage}%",
            "completed_domains": completed_count,
            "total_domains": len(checklist)
        }
