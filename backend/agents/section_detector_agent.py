import re
from typing import Dict, Any, List


class SectionDetectorAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        # Dictionary of heading patterns (case insensitive)
        self.section_patterns = {
            "CHIEF_COMPLAINT": r"(chief complaint|complains of|cc\b)",
            "HISTORY_OF_PRESENT_ILLNESS": r"(history of present illness|hpi\b)",
            "PAST_MEDICAL_HISTORY": r"(past medical history|medical history|pmh\b|history\b)",
            "MEDICATIONS": r"(current medications|medications|medication list|prescription\b|meds\b)",
            "ALLERGIES": r"(allergies|allergy\b)",
            "VITALS": r"(vital signs|vitals\b|vital\b)",
            "LABORATORY": r"(laboratory findings|labs\b|laboratory results|lab results|laboratory\b|laboratory values\b)",
            "ASSESSMENT": r"(assessment\b|impression\b|diagnosis\b)",
            "PLAN": r"(plan\b|recommendation\b|treatment plan\b|follow-up\b)"
        }

    def detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Detects headings and splits text into logical ranges.
        Returns a list of dicts with keys: name, start, end, text.
        """
        matches = []
        text_len = len(text)
        
        for sec_name, pattern in self.section_patterns.items():
            for m in re.finditer(pattern, text, re.IGNORECASE):
                start = m.start()
                pre_text = text[max(0, start-10):start]
                post_text = text[m.end():m.end()+10]
                
                is_heading = False
                if start == 0 or "\n" in pre_text or ":" in pre_text:
                    is_heading = True
                if ":" in post_text or "\n" in post_text:
                    is_heading = True
                
                if is_heading:
                    matches.append((start, sec_name, m.group(0)))
        
        matches.sort()
        
        sections = []
        if not matches:
            return [{
                "name": "UNKNOWN",
                "start": 0,
                "end": text_len,
                "text": text
            }]
            
        for i in range(len(matches)):
            start_pos, sec_name, header = matches[i]
            content_start = start_pos + len(header)
            end_pos = matches[i+1][0] if i + 1 < len(matches) else text_len
            
            sections.append({
                "name": sec_name,
                "start": start_pos,
                "end": end_pos,
                "text": text[content_start:end_pos].strip()
            })
            
        if matches[0][0] > 0:
            sections.insert(0, {
                "name": "UNKNOWN",
                "start": 0,
                "end": matches[0][0],
                "text": text[0:matches[0][0]].strip()
            })
            
        return sections
