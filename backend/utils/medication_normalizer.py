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
    "weekly": ("Weekly", "Once Weekly"),
    "once weekly": ("Weekly", "Once Weekly"),
    "monthly": ("Monthly", "Once Monthly"),
    "once monthly": ("Monthly", "Once Monthly"),
    "hs": ("HS", "At Bedtime"),
    "at bedtime": ("HS", "At Bedtime"),
    "bedtime": ("HS", "At Bedtime"),
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
    "in the morning": "Morning",
    "evening": "Evening",
    "in the evening": "Evening",
    "night": "Night",
    "in the night": "Night",
    "bedtime": "Bedtime",
    "at bedtime": "Bedtime",
    "hs": "Bedtime",
}

class MedicationNormalizer:
    """
    Normalizes clinical prescription attributes using KnowledgeLoader dynamic configuration files.
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
        try:
            from backend.knowledge.knowledge_loader import KnowledgeLoader
            routes = KnowledgeLoader().get_route_dict()
            if r_low in routes:
                return routes[r_low]
        except Exception:
            pass
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

        # Check dynamic KnowledgeLoader frequency dictionary
        try:
            from backend.knowledge.knowledge_loader import KnowledgeLoader
            freqs = KnowledgeLoader().get_frequency_dict()
            if f_low in freqs:
                item = freqs[f_low]
                return {"code": item["code"], "description": item["normalized"]}
        except Exception:
            pass

        # Fallback to direct lookup map
        if f_low in _FREQ_MAP:
            code, desc = _FREQ_MAP[f_low]
            return {"code": code, "description": desc}

        # Check hourly patterns (e.g., q6h, q8h, q6h PRN, every 6 hours)
        m = re.search(r'(?:every\s+(?P<num>\d+)\s*hours?|q(?P<qnum>\d+)h)', f_low)
        if m:
            n = m.group("num") or m.group("qnum")
            code = f"q{n}h"
            if "prn" in f_low or "sos" in f_low:
                code += " PRN"
            return {"code": code, "description": f"Every {n} Hours As Needed" if "prn" in code else f"Every {n} Hours"}

        return {"code": raw_freq.strip().upper(), "description": raw_freq.strip()}

    @classmethod
    def normalize_timing(cls, raw_timing: str) -> str:
        if not raw_timing:
            return "Unspecified"
        t_low = raw_timing.strip().lower()
        try:
            from backend.knowledge.knowledge_loader import KnowledgeLoader
            timings = KnowledgeLoader().get_timing_dict()
            if t_low in timings:
                return timings[t_low]
        except Exception:
            pass
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

    @classmethod
    def normalize_duration(cls, raw_duration: str) -> Dict[str, Any]:
        """
        Normalizes raw duration text into standard representation and total days count.
        e.g., 'for 5 days' -> {'text': 'For 5 days', 'days': 5}
              'x7 days' -> {'text': 'For 7 days', 'days': 7}
              '2 weeks' -> {'text': 'For 2 weeks (14 days)', 'days': 14}
              '1 month' -> {'text': 'For 1 month (30 days)', 'days': 30}
        """
        if not raw_duration or raw_duration.strip().lower() in ("not specified", "n/a", "none"):
            return {"text": "Not Specified", "days": None}

        clean = raw_duration.strip()
        low = clean.lower()

        word_to_num = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "eleven": 11, "twelve": 12
        }

        # Check days
        m_day = re.search(r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*days?', low)
        if m_day:
            val_str = m_day.group(1)
            days = int(val_str) if val_str.isdigit() else word_to_num.get(val_str, 1)
            return {"text": f"For {days} days", "days": days}

        # Check weeks
        m_week = re.search(r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*weeks?', low)
        if m_week:
            val_str = m_week.group(1)
            weeks = int(val_str) if val_str.isdigit() else word_to_num.get(val_str, 1)
            days = weeks * 7
            return {"text": f"For {weeks} week{'s' if weeks > 1 else ''} ({days} days)", "days": days}

        # Check months
        m_month = re.search(r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*months?', low)
        if m_month:
            val_str = m_month.group(1)
            months = int(val_str) if val_str.isdigit() else word_to_num.get(val_str, 1)
            days = months * 30
            return {"text": f"For {months} month{'s' if months > 1 else ''} ({days} days)", "days": days}

        if any(kw in low for kw in ["continue", "lifelong", "long-term", "until finished"]):
            return {"text": clean.title(), "days": None}

        return {"text": clean, "days": None}

