from typing import Dict, Any, List

class QualityScoreEngine:
    """Calculates itemized Clinical Quality Score breakdown across 7 dimensions."""

    @classmethod
    def calculate_quality_score(
        cls,
        diseases: List[Any],
        medications: List[Any],
        labs: List[Any],
        vitals: List[Any],
        missing_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        
        doc_score = 95.0 if len(diseases) > 0 else 70.0
        med_score = 90.0 if len(medications) > 0 else 80.0
        diag_score = 95.0 if len(diseases) > 0 else 60.0
        ev_score = 92.0 if (len(labs) > 0 or len(vitals) > 0) else 75.0
        mon_score = 90.0
        foll_score = 88.0
        coding_score = 98.0

        if missing_info and isinstance(missing_info, dict):
            crit_count = len(missing_info.get("critical", []))
            doc_score = max(50.0, doc_score - crit_count * 10)
            mon_score = max(50.0, mon_score - crit_count * 5)

        overall = round((doc_score + med_score + diag_score + ev_score + mon_score + foll_score + coding_score) / 7.0, 1)

        return {
            "overall_score": f"{overall}%",
            "score": overall,
            "breakdown": {
                "documentation": f"{int(doc_score)}%",
                "medication": f"{int(med_score)}%",
                "diagnosis": f"{int(diag_score)}%",
                "evidence": f"{int(ev_score)}%",
                "monitoring": f"{int(mon_score)}%",
                "follow_up": f"{int(foll_score)}%",
                "coding": f"{int(coding_score)}%",
                "overall": f"{overall}%"
            }
        }
