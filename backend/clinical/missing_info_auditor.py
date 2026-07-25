from typing import Dict, Any, List

class MissingInfoAuditor:
    """Audits clinical notes for missing data categorized into Critical, Important, and Optional missing items."""

    @classmethod
    def audit_missing_information(
        cls,
        text: str,
        diseases: List[str],
        labs: List[Any],
        vitals: List[Any],
        medications: List[Any]
    ) -> Dict[str, Any]:
        text_low = text.lower()
        critical = []
        important = []
        optional = []

        dis_str = " ".join(diseases).lower()

        # History Checks
        if "pack" not in text_low and "smok" not in text_low:
            important.append("Smoking Pack-Years History & Quit Date")
        if "family" not in text_low:
            optional.append("Family History of Premature CAD / Sudden Death")

        # Vitals Checks
        if "bmi" not in text_low and "weight" not in text_low:
            important.append("Patient Weight & BMI Measurement")
        if "spo2" not in text_low and ("copd" in dis_str or "pneumonia" in dis_str or "heart failure" in dis_str):
            critical.append("Pulse Oximetry (SpO2%)")

        # Labs Checks
        if "potassium" in text_low or "hyperkalemia" in dis_str:
            important.append("Repeat Serum Potassium post-therapy evaluation")
            important.append("Serum Magnesium Level (critical for refractory hyperkalemia)")

        if "stemi" in dis_str or "infarction" in dis_str:
            if "troponin" not in text_low:
                critical.append("Serial Troponin Trend (0h, 3h, 6h)")

        # Medication Checks
        has_dur = any(m.get("duration") for m in medications if isinstance(m, dict))
        if not has_dur:
            important.append("Medication Duration & Discontinuation Dates")

        return {
            "critical": critical if critical else ["No critical missing clinical fields detected"],
            "important": important,
            "optional": optional,
            "history": important,
            "labs": [l for l in important if "Serum" in l or "Troponin" in l or "Potassium" in l],
            "vitals": [v for v in critical if "SpO2" in v] + [v for v in important if "BMI" in v]
        }
