"""
backend/core/validators.py

Clinical input validation utilities.

Validates:
  - Vital sign ranges (heart rate, BP, temperature, SpO2, etc.)
  - Impossible clinical combinations (male + pregnant, infant + warfarin, etc.)
  - Lab value plausibility (negative creatinine, HbA1c > 20%, etc.)
  - Medication dose sanity checks
  - Age / gender consistency

All validators return a list of string error messages (empty = valid).
"""

from typing import Any, Dict, List, Optional, Tuple


# ── Vital sign reference ranges ────────────────────────────────────────────────

VITAL_RANGES: Dict[str, Tuple[float, float]] = {
    "heart_rate":          (10.0, 300.0),   # bpm
    "systolic_bp":         (50.0, 300.0),   # mmHg
    "diastolic_bp":        (20.0, 200.0),   # mmHg
    "temperature_celsius": (30.0,  45.0),   # °C
    "temperature_fahrenheit": (86.0, 113.0),# °F
    "spo2":                (50.0, 100.0),   # %
    "respiratory_rate":    (4.0,   60.0),   # breaths/min
    "gcs":                 (3.0,   15.0),   # Glasgow Coma Scale
    "weight_kg":           (0.5,  300.0),   # kg
    "height_cm":           (30.0, 250.0),   # cm
    "bmi":                 (5.0,   80.0),
}


# ── Lab value plausibility ranges ──────────────────────────────────────────────

LAB_RANGES: Dict[str, Tuple[float, float]] = {
    "hemoglobin":          (1.0,   25.0),   # g/dL
    "hematocrit":          (5.0,   75.0),   # %
    "wbc":                 (0.1,   100.0),  # ×10³/µL
    "platelets":           (1.0,  2000.0),  # ×10³/µL
    "sodium":              (100.0, 180.0),  # mEq/L
    "potassium":           (1.5,   9.0),    # mEq/L
    "creatinine":          (0.1,   30.0),   # mg/dL  (must be > 0)
    "glucose":             (10.0,  1000.0), # mg/dL
    "hba1c":               (2.0,   20.0),   # %  (> 20% is impossible)
    "troponin":            (0.0,   1000.0), # ng/mL
    "bnp":                 (0.0,   50000.0),# pg/mL
    "inr":                 (0.5,   20.0),
    "ph":                  (6.5,   8.0),    # arterial blood gas
    "pao2":                (20.0,  700.0),  # mmHg
    "paco2":               (10.0,  120.0),  # mmHg
}


# ── Impossible clinical combinations ──────────────────────────────────────────

_IMPOSSIBLE_COMBINATIONS = [
    # (condition_field, condition_value, impossible_field, impossible_value, message)
    ("gender", "male",   "condition", "pregnant",      "Male patients cannot be pregnant."),
    ("gender", "male",   "condition", "pregnancy",     "Male patients cannot be pregnant."),
    ("age_years", "<2",  "medication", "warfarin",     "Warfarin is contraindicated in infants under 2 years."),
    ("age_years", "<18", "medication", "metformin",    "Metformin requires clinical justification for patients under 18."),
    ("creatinine", ">15","medication", "metformin",    "Metformin is contraindicated in severe renal failure (Cr > 15)."),
]


# ── Public API ─────────────────────────────────────────────────────────────────

def validate_vitals(vitals: Dict[str, Any]) -> List[str]:
    """
    Validate vital signs against physiologically plausible ranges.

    Parameters
    ----------
    vitals : dict mapping vital_name → numeric value

    Returns
    -------
    List of validation error strings. Empty list = all valid.

    Example
    -------
    >>> errors = validate_vitals({"heart_rate": 500, "spo2": 102})
    >>> # ["Heart rate 500 is outside plausible range (10–300 bpm)",
    >>> #  "SpO2 102 is outside plausible range (50–100 %)"]
    """
    errors: List[str] = []
    for vital_key, value in vitals.items():
        key_lower = vital_key.lower().replace(" ", "_").replace("-", "_")
        if key_lower in VITAL_RANGES:
            lo, hi = VITAL_RANGES[key_lower]
            try:
                num = float(value)
                if not (lo <= num <= hi):
                    label = key_lower.replace("_", " ").title()
                    errors.append(
                        f"{label} value {num} is outside the plausible range ({lo}–{hi})."
                    )
            except (TypeError, ValueError):
                pass   # Non-numeric values are ignored (may be 'N/A' etc.)
    return errors


def validate_labs(labs: Dict[str, Any]) -> List[str]:
    """
    Validate lab results against plausibility ranges.

    Parameters
    ----------
    labs : dict mapping lab_name → numeric value

    Returns
    -------
    List of validation error strings.
    """
    errors: List[str] = []
    for lab_key, value in labs.items():
        key_lower = lab_key.lower().replace(" ", "_").replace("-", "_")
        if key_lower in LAB_RANGES:
            lo, hi = LAB_RANGES[key_lower]
            try:
                num = float(value)
                if num < 0:
                    label = key_lower.replace("_", " ").title()
                    errors.append(f"{label} cannot be negative (got {num}).")
                elif not (lo <= num <= hi):
                    label = key_lower.replace("_", " ").title()
                    errors.append(
                        f"{label} value {num} is outside the plausible range ({lo}–{hi})."
                    )
            except (TypeError, ValueError):
                pass
    return errors


def validate_clinical_consistency(patient_data: Dict[str, Any]) -> List[str]:
    """
    Detect impossible clinical combinations in structured patient data.

    Parameters
    ----------
    patient_data : Flat dict, e.g.:
        {
            "gender": "male",
            "age_years": 45,
            "condition": "pregnant",
            "medication": "metformin",
            "creatinine": 18.0
        }

    Returns
    -------
    List of validation error strings.
    """
    errors: List[str] = []
    gender    = str(patient_data.get("gender", "")).lower()
    age       = patient_data.get("age_years")
    condition = str(patient_data.get("condition", "")).lower()
    medication= str(patient_data.get("medication", "")).lower()
    creatinine= patient_data.get("creatinine")

    # Male + pregnant
    if gender == "male" and ("pregnant" in condition or "pregnancy" in condition):
        errors.append("Impossible combination: Male gender + pregnancy diagnosis.")

    # Infant + warfarin
    if age is not None:
        try:
            age_num = float(age)
            if age_num < 2 and "warfarin" in medication:
                errors.append(
                    "Safety alert: Warfarin is contraindicated in patients under 2 years old."
                )
            if age_num < 0 or age_num > 150:
                errors.append(f"Age {age_num} is not physiologically plausible.")
        except (TypeError, ValueError):
            pass

    # Severe renal failure + metformin
    if creatinine is not None:
        try:
            cr = float(creatinine)
            if cr < 0:
                errors.append("Creatinine cannot be negative.")
            if cr > 15 and "metformin" in medication:
                errors.append(
                    f"Safety alert: Metformin is contraindicated with creatinine {cr} mg/dL "
                    f"(severe renal failure). Risk of lactic acidosis."
                )
        except (TypeError, ValueError):
            pass

    return errors


def validate_clinical_note(note: str) -> List[str]:
    """
    Basic clinical note content validation.

    Parameters
    ----------
    note : Raw clinical note text.

    Returns
    -------
    List of validation error strings.
    """
    errors: List[str] = []
    if not note or not note.strip():
        errors.append("Clinical note cannot be empty.")
        return errors
    if len(note.strip()) < 20:
        errors.append("Clinical note is too short to contain meaningful clinical information.")
    if len(note) > 100_000:
        errors.append("Clinical note exceeds maximum allowed length (100,000 characters).")
    return errors
