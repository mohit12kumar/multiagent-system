from typing import Dict, Any, Tuple

class UnitNormalizationEngine:
    """Standardizes laboratory & vital sign units and flags implausible readings (e.g. 39.2°F)."""

    UNIT_CONVERSIONS = {
        "mg/dl": "mg/dL",
        "mmol/l": "mmol/L",
        "ml/min": "mL/min",
        "pg/ml": "pg/mL",
        "ng/ml": "ng/mL",
        "meq/l": "mEq/L",
        "g/dl": "g/dL",
        "umol/l": "μmol/L"
    }

    @classmethod
    def normalize_unit(cls, unit: str) -> str:
        if not unit:
            return ""
        return cls.UNIT_CONVERSIONS.get(unit.strip().lower(), unit.strip())

    @classmethod
    def parse_temperature(cls, raw_value: str, raw_unit: str = "C") -> Dict[str, Any]:
        try:
            val = float(raw_value)
        except (ValueError, TypeError):
            return {
                "display": f"{raw_value} {raw_unit}".strip(),
                "status": "Unknown",
                "is_implausible": False
            }

        unit_clean = raw_unit.strip().upper() if raw_unit else "C"

        if "F" in unit_clean:
            if val < 70.0: # e.g. 39.2 F
                return {
                    "display": f"{val} °F",
                    "status": "Implausible Value (Possible unit mismatch, presumed 39.2°C Fever)",
                    "is_implausible": True,
                    "suggested_interpretation": f"{val} °C (Fever / Hyperthermia)"
                }
            elif val > 99.5:
                return {"display": f"{val} °F", "status": "Fever (Hyperthermia)", "is_implausible": False}
            elif val < 95.0:
                return {"display": f"{val} °F", "status": "Hypothermia", "is_implausible": False}
            else:
                return {"display": f"{val} °F", "status": "Normal Body Temperature", "is_implausible": False}
        else:
            if val > 37.5:
                return {"display": f"{val} °C", "status": "Fever (Hyperthermia)", "is_implausible": False}
            elif val < 35.0:
                return {"display": f"{val} °C", "status": "Hypothermia", "is_implausible": False}
            else:
                return {"display": f"{val} °C", "status": "Normal Body Temperature", "is_implausible": False}
