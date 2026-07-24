from typing import Dict, Any, Optional

class PrescriptionChecker:
    """Audits prescription quality across Name, Dose, Frequency, Route, and Duration, calculating a Completeness Score (%)."""

    @classmethod
    def audit_prescription(
        cls,
        medication_name: str,
        dosage: Optional[str] = None,
        frequency: Optional[str] = None,
        route: Optional[str] = None,
        duration: Optional[str] = None
    ) -> Dict[str, Any]:

        valid_name = bool(medication_name and medication_name.strip() and medication_name.lower() != "n/a")
        valid_dose = bool(dosage and dosage.strip() and dosage.lower() not in ("n/a", "none", "unspecified"))
        valid_freq = bool(frequency and frequency.strip() and frequency.lower() not in ("n/a", "none", "unspecified"))
        valid_route = bool(route and route.strip() and route.lower() not in ("n/a", "none", "unspecified"))
        valid_dur = bool(duration and duration.strip() and duration.lower() not in ("n/a", "none", "unspecified"))

        # Score calculation: Name (30%), Dose (25%), Frequency (20%), Route (15%), Duration (10%)
        score = (30 if valid_name else 0) + (25 if valid_dose else 0) + (20 if valid_freq else 0) + (15 if valid_route else 0) + (10 if valid_dur else 0)

        missing_fields = []
        if not valid_dose: missing_fields.append("Dose")
        if not valid_freq: missing_fields.append("Frequency")
        if not valid_route: missing_fields.append("Route")
        if not valid_dur: missing_fields.append("Duration")

        return {
            "medication": medication_name,
            "dose_status": "Correct" if valid_dose else "Missing",
            "frequency_status": "Correct" if valid_freq else "Missing",
            "route_status": "Correct" if valid_route else "Default (Oral)",
            "duration_status": "Correct" if valid_dur else "Missing",
            "completeness_score": f"{score}%",
            "score_numeric": score,
            "missing_elements": missing_fields,
            "quality_rating": "High Quality" if score >= 80 else ("Moderate" if score >= 60 else "Incomplete")
        }
