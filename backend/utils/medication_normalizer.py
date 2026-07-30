"""
backend/utils/medication_normalizer.py

Normalizes clinical prescription attributes (Route, Frequency, Dose, Timing) into standard enterprise representations.
Also provides Numeric Schedule Parsing (1-0-1 -> BID / Twice Daily).
"""

import re
from typing import Dict, Any, Tuple

# ── ROUTE NORMALIZATION MAP ───────────────────────────────────────────────────
_ROUTE_MAP: Dict[str, str] = {
    "po": "PO",
    "oral": "PO",
    "orally": "PO",
    "by mouth": "PO",
    "iv": "IV",
    "intravenous": "IV",
    "intravenously": "IV",
    "im": "IM",
    "intramuscular": "IM",
    "intramuscularly": "IM",
    "sc": "SC",
    "sq": "SC",
    "subcutaneous": "SC",
    "subcutaneously": "SC",
    "topical": "Topical",
    "topically": "Topical",
    "cream": "Topical",
    "gel": "Topical",
    "ointment": "Topical",
    "eye drop": "Ophthalmic",
    "eye drops": "Ophthalmic",
    "ear drop": "Otic",
    "ear drops": "Otic",
    "nasal spray": "Nasal",
    "inhalation": "Inhalation",
    "inhaled": "Inhalation",
    "nebulization": "Inhalation",
    "nebulised": "Inhalation",
    "puff": "Inhalation",
    "puffs": "Inhalation",
    "suppository": "Rectal",
    "rectal": "Rectal",
    "rectally": "Rectal",
}

# ── FREQUENCY NORMALIZATION MAP ───────────────────────────────────────────────
_FREQ_MAP: Dict[str, Tuple[str, str]] = {
    # Abbreviation -> (Code, Human Readable)
    "od": ("OD", "Once Daily"),
    "once daily": ("OD", "Once Daily"),
    "daily": ("OD", "Once Daily"),
    "every day": ("OD", "Once Daily"),
    "qd": ("OD", "Once Daily"),
    "bd": ("BID", "Twice Daily"),
    "bid": ("BID", "Twice Daily"),
    "twice daily": ("BID", "Twice Daily"),
    "morning and evening": ("BID", "Twice Daily"),
    "tds": ("TDS", "Three Times Daily"),
    "tid": ("TID", "Three Times Daily"),
    "thrice daily": ("TDS", "Three Times Daily"),
    "three times daily": ("TDS", "Three Times Daily"),
    "qid": ("QID", "Four Times Daily"),
    "qds": ("QDS", "Four Times Daily"),
    "four times daily": ("QID", "Four Times Daily"),
    "qod": ("QOD", "Every Other Day"),
    "alternate day": ("QOD", "Every Other Day"),
    "every other day": ("QOD", "Every Other Day"),
    "weekly": ("QWK", "Weekly"),
    "monthly": ("QMO", "Monthly"),
    "hs": ("HS", "At Bedtime"),
    "at bedtime": ("HS", "At Bedtime"),
    "night": ("HS", "At Bedtime"),
    "stat": ("STAT", "Immediately"),
    "prn": ("PRN", "As Needed"),
    "sos": ("SOS", "As Needed"),
    "as needed": ("PRN", "As Needed"),
    "as required": ("PRN", "As Needed"),
    "if needed": ("PRN", "As Needed"),
    "when required": ("PRN", "As Needed"),
}

# ── TIMING NORMALIZATION MAP ──────────────────────────────────────────────────
_TIMING_MAP: Dict[str, str] = {
    "ac": "Before meals (AC)",
    "before meals": "Before meals (AC)",
    "before meal": "Before meals (AC)",
    "before breakfast": "Before breakfast",
    "before lunch": "Before lunch",
    "before dinner": "Before dinner",
    "pc": "After meals (PC)",
    "after meals": "After meals (PC)",
    "after meal": "After meals (PC)",
    "after breakfast": "After breakfast",
    "after lunch": "After lunch",
    "after dinner": "After dinner",
    "with meals": "With meals",
    "with meal": "With meals",
    "with food": "With food",
    "empty stomach": "Empty stomach",
    "morning": "Morning",
    "evening": "Evening",
    "night": "Night",
    "bedtime": "Bedtime (HS)",
    "hs": "Bedtime (HS)",
}

class MedicationNormalizer:
    """
    Normalizes medication attributes.
    """

    @classmethod
    def parse_numeric_schedule(cls, pattern: str) -> Dict[str, str]:
        """
        Parses numeric schedules like 1-0-1, 1-1-1, 1-0-0, 0-0-1, 2-2-2.
        Returns {"original": pattern, "normalized": code, "description": human_readable}
        """
        clean = pattern.strip()
        parts = clean.split("-")
        if len(parts) >= 3:
            try:
                m = sum(float(p) for p in parts if p and p != '0')
            except ValueError:
                m = 0.0

            if clean in ("1-0-0", "0.5-0-0", "1/2-0-0"):
                return {"original": clean, "normalized": "OD", "description": "Once Daily Morning"}
            elif clean in ("0-0-1", "0-0-0.5", "0-0-1/2"):
                return {"original": clean, "normalized": "HS", "description": "Once Daily Night"}
            elif clean in ("0-1-0", "0-0.5-0"):
                return {"original": clean, "normalized": "OD", "description": "Once Daily Afternoon"}
            elif clean in ("1-0-1", "0.5-0-0.5", "1/2-0-1/2"):
                return {"original": clean, "normalized": "BID", "description": "Twice Daily"}
            elif clean in ("1-1-1", "1/2-1/2-1/2"):
                return {"original": clean, "normalized": "TDS", "description": "Three Times Daily"}
            elif clean in ("1-1-1-1", "2-2-2-2"):
                return {"original": clean, "normalized": "QID", "description": "Four Times Daily"}

        return {"original": clean, "normalized": "BID" if "1-0-1" in clean else "OD", "description": clean}

    @classmethod
    def normalize_route(cls, raw_route: str) -> str:
        if not raw_route:
            return "PO"
        r_low = raw_route.strip().lower()
        return _ROUTE_MAP.get(r_low, raw_route.strip().upper())

    @classmethod
    def normalize_frequency(cls, raw_freq: str) -> Dict[str, str]:
        if not raw_freq:
            return {"code": "OD", "description": "Once Daily"}

        f_low = raw_freq.strip().lower()

        # Check numeric schedule first (e.g., 1-0-1)
        if re.match(r'^[0-9/\.]+(?:-[0-9/\.]+){2,3}$', f_low):
            num_res = cls.parse_numeric_schedule(f_low)
            return {"code": num_res["normalized"], "description": num_res["description"]}

        # Check direct lookup map
        if f_low in _FREQ_MAP:
            code, desc = _FREQ_MAP[f_low]
            return {"code": code, "description": desc}

        # Check hourly patterns (e.g., q8h, every 8 hours)
        m = re.search(r'(?:every\s+(?P<num>\d+)\s*hours?|q(?P<qnum>\d+)h)', f_low)
        if m:
            n = m.group("num") or m.group("qnum")
            return {"code": f"Q{n}H", "description": f"Every {n} Hours"}

        return {"code": raw_freq.strip().upper(), "description": raw_freq.strip()}

    @classmethod
    def normalize_timing(cls, raw_timing: str) -> str:
        if not raw_timing:
            return "Unspecified"
        t_low = raw_timing.strip().lower()
        return _TIMING_MAP.get(t_low, raw_timing.strip().title())

    @classmethod
    def normalize_dose(cls, raw_dose: str) -> str:
        if not raw_dose:
            return "Unspecified"
        clean = raw_dose.strip()
        # Add space between digit and unit if missing (e.g., 500mg -> 500 mg, 250ug -> 250 mcg)
        clean = re.sub(r'(\d+(?:\.\d+)?)\s*([a-zA-Zμ]+)', r'\1 \2', clean)
        # Normalize microgram symbol
        clean = clean.replace("μg", "mcg").replace("ug", "mcg")
        return clean
