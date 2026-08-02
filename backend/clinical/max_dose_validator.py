"""
backend/clinical/max_dose_validator.py

Maximum Daily Dose Safety Validator.
Calculates 24-hour cumulative dosage for prescribed drugs and flags toxic overdose warnings
(e.g., Paracetamol > 4000 mg/day, Metformin > 2550 mg/day, Amlodipine > 10 mg/day).
"""

import re
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("multiagent_ner")

# Maximum recommended 24-hour daily limits in mg (or IU for vitamins)
_MAX_DAILY_DOSES: Dict[str, Tuple[float, str]] = {
    "paracetamol": (4000.0, "mg"),
    "acetaminophen": (4000.0, "mg"),
    "metformin": (2550.0, "mg"),
    "amlodipine": (10.0, "mg"),
    "atorvastatin": (80.0, "mg"),
    "rosuvastatin": (40.0, "mg"),
    "aspirin": (325.0, "mg"),
    "ecosprin": (325.0, "mg"),
    "ibuprofen": (3200.0, "mg"),
    "diclofenac": (150.0, "mg"),
    "salbutamol": (32.0, "mg"),
    "vitamin d3": (60000.0, "IU")
}

_FREQ_TIMES_PER_DAY: Dict[str, float] = {
    "OD": 1.0, "QD": 1.0, "DAILY": 1.0,
    "BID": 2.0, "BD": 2.0, "TWICE DAILY": 2.0,
    "TDS": 3.0, "TID": 3.0, "THREE TIMES DAILY": 3.0,
    "QID": 4.0, "QDS": 4.0, "FOUR TIMES DAILY": 4.0,
    "Q6H": 4.0, "Q8H": 3.0, "Q12H": 2.0,
    "HS": 1.0, "SOS": 1.0, "PRN": 1.0, "STAT": 1.0,
    "WEEKLY": 0.14, "ONCE WEEKLY": 0.14
}

class MaxDoseValidator:
    """
    Validates cumulative 24-hour drug dosages against safety thresholds.
    """

    @classmethod
    def validate_medications(cls, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scans a list of medication dictionaries for overdose warnings.
        """
        warnings = []
        for m in medications:
            name = (m.get("name") or m.get("generic_name") or "").lower().strip()
            dose_str = str(m.get("dose", ""))
            freq_str = str(m.get("frequency", "")).upper().strip()

            # Parse numeric dose
            num_m = re.search(r'(\d+(?:\.\d+)?)', dose_str)
            if not num_m:
                continue

            single_dose = float(num_m.group(1))
            multiplier = _FREQ_TIMES_PER_DAY.get(freq_str, 1.0)
            daily_dose = single_dose * multiplier

            # Lookup max limit
            for drug_key, (max_limit, unit) in _MAX_DAILY_DOSES.items():
                if drug_key in name:
                    if daily_dose > max_limit:
                        warn = {
                            "drug": m.get("name"),
                            "calculated_daily_dose": f"{daily_dose:g} {unit}",
                            "max_safe_limit": f"{max_limit:g} {unit}",
                            "severity": "CRITICAL_OVERDOSE",
                            "message": f"Calculated 24h dose of {daily_dose:g} {unit} exceeds max safe limit of {max_limit:g} {unit} for {m.get('name')}."
                        }
                        warnings.append(warn)
                        logger.warning(f"[MaxDoseValidator] Overdose alert: {warn['message']}")
                    break

        return warnings
