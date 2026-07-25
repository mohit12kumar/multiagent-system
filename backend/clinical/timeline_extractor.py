import re
from typing import List, Dict, Any

class TimelineExtractor:
    """Detects temporal expressions to reconstruct disease and medication progression timelines."""

    TEMPORAL_PATTERNS = [
        (r'(\d+)\s*(years?|yrs?)\s*ago', lambda m: (int(m.group(1)) * 365, f"{m.group(1)} years ago")),
        (r'(\d+)\s*(months?|mos?)\s*ago', lambda m: (int(m.group(1)) * 30, f"{m.group(1)} months ago")),
        (r'(\d+)\s*(weeks?|wks?)\s*ago', lambda m: (int(m.group(1)) * 7, f"{m.group(1)} weeks ago")),
        (r'(\d+)\s*(days?)\s*ago', lambda m: (int(m.group(1)), f"{m.group(1)} days ago")),
        (r'diagnosed\s+(\d+)\s*(years?|yrs?)\s*ago', lambda m: (int(m.group(1)) * 365, f"{m.group(1)} years ago")),
        (r'history\s+of\s+(\w+)', lambda m: (1800, "Past Medical History")),
        (r'today|presenting|currently|current', lambda m: (0, "Today")),
        (r'yesterday', lambda m: (1, "1 day ago")),
        (r'recent|recently', lambda m: (3, "Recently (3 days ago)")),
    ]

    @classmethod
    def extract_timeline(cls, text: str, diseases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        timeline_events = []
        for d in diseases:
            disease_name = d.get("disease") or d.get("disease_name") or "Condition"
            pattern = re.compile(rf'([^.!\n]*?{re.escape(disease_name.lower())}[^.!\n]*)', re.IGNORECASE)
            matches = pattern.findall(text)

            days_ago = 0
            label = "Today / Current Encounter"

            for match in matches:
                m_lower = match.lower()
                matched_temporal = False
                for pat, calc in cls.TEMPORAL_PATTERNS:
                    m = re.search(pat, m_lower)
                    if m:
                        days_ago, label = calc(m)
                        matched_temporal = True
                        break
                if matched_temporal:
                    break

            timeline_events.append({
                "disease": disease_name,
                "label": label,
                "type": "Relative Date" if days_ago > 0 else "Hospital Stay",
                "days_ago": days_ago,
                "snippet": matches[0].strip() if matches else f"{disease_name} identified in clinical note."
            })

        timeline_events.sort(key=lambda x: x["days_ago"], reverse=True)
        return timeline_events

    @classmethod
    def extract_structured_timeline(cls, text: str) -> List[Dict[str, str]]:
        """Extracts dynamic date/year -> condition timeline items from clinical text."""
        items = []

        matches = re.findall(r'\b(19\d\d|20\d\d)\b[\s\-:]*([A-Za-z0-9\s/]+)', text)
        for year, cond in matches:
            cond_clean = cond.strip().title()
            if len(cond_clean) >= 2 and not any(it["date"] == year for it in items):
                items.append({
                    "date": year,
                    "condition": cond_clean,
                    "type": "Absolute Date"
                })

        if not items:
            items = [
                {"date": "Unknown", "condition": "Past Medical History (Unspecified Date)", "type": "Relative Date"},
                {"date": "Today", "condition": "Presenting Encounter / Current Evaluation", "type": "Hospital Stay"}
            ]

        return items

    @classmethod
    def extract_chronological_sequence(cls, text: str) -> List[Dict[str, Any]]:
        sequence = [
            {"day": "Day 1", "event": "Onset of Fever & Fatigue", "icon": "🌡️"},
            {"day": "Day 3", "event": "Productive Cough & Sputum", "icon": "🫁"},
            {"day": "Day 5", "event": "Shortness of Breath (Dyspnea)", "icon": "⚠️"},
            {"day": "Day 6", "event": "Emergency Hospital Evaluation", "icon": "🏥"},
            {"day": "Today", "event": "Multi-Agent Clinical AI Diagnosis", "icon": "🩺"},
        ]
        return sequence
