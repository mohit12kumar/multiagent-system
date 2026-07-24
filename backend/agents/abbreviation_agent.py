import re
from typing import Dict, Any

class MedicalAbbreviationAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        # Extended dictionary of standard medical abbreviations and shorthand
        self.abbreviation_map = {
            "htn": "hypertension",
            "t2dm": "type 2 diabetes",
            "t1dm": "type 1 diabetes",
            "dm": "diabetes",
            "ckd": "chronic kidney disease",
            "cad": "coronary artery disease",
            "chf": "congestive heart failure",
            "copd": "chronic obstructive pulmonary disease",
            "afib": "atrial fibrillation",
            "af": "atrial fibrillation",
            "ami": "acute myocardial infarction",
            "mi": "myocardial infarction",
            "aki": "acute kidney injury",
            "gerd": "gastroesophageal reflux disease",
            "uti": "urinary tract infection",
            "sob": "shortness of breath",
            "doe": "dyspnea on exertion",
            "pnd": "paroxysmal nocturnal dyspnea",
            "cap": "community acquired pneumonia",
            "ards": "acute respiratory distress syndrome",
            "dvt": "deep vein thrombosis",
            "pe": "pulmonary embolism",
            "cva": "cerebrovascular accident",
            "tia": "transient ischemic attack",
            "qd": "once daily",
            "bid": "twice daily",
            "tid": "three times daily",
            "qid": "four times daily",
            "hs": "nightly",
            "po": "oral",
            "prn": "as needed",
            "od": "once daily",
            "bd": "twice daily"
        }

        # Multi-language / Hinglish translation & standardization rules
        self.hinglish_phrases = [
            (r'\bpatient\s+ko\s+fever\s+hai\b', 'Patient presents with fever'),
            (r'\bpatient\s+ko\s+bukhar\s+hai\b', 'Patient presents with fever'),
            (r'\bbp\s+jyada\s+hai\b', 'Elevated blood pressure (hypertension)'),
            (r'\bbp\s+high\s+hai\b', 'High blood pressure (hypertension)'),
            (r'\bsar\s+dard\s+hai\b', 'Patient reports headache'),
            (r'\bsaans\s+lene\s+me\s+taklif\b', 'Dyspnea and shortness of breath'),
            (r'\bkaasi\s+hai\b', 'Productive cough'),
            (r'\bchakkar\s+a\s+raha\s+hai\b', 'Patient reports dizziness'),
        ]

    def expand_abbreviations(self, text: str) -> str:
        """Replaces clinical abbreviations and translates Hinglish expressions into standard medical terms."""
        if not text:
            return ""

        processed = text

        # 1. Multi-language / Hinglish phrase expansion
        for pattern, replacement in self.hinglish_phrases:
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        # 2. Tokenize and replace clinical abbreviations
        words = re.findall(r'\b\w+\b|\s+|[^\w\s]', processed)
        result = []
        for word in words:
            word_lower = word.lower()
            if word_lower in self.abbreviation_map:
                expanded = self.abbreviation_map[word_lower]
                if word.isupper():
                    result.append(expanded.upper())
                elif word[0].isupper():
                    result.append(expanded.title())
                else:
                    result.append(expanded)
            else:
                result.append(word)
        return "".join(result)
