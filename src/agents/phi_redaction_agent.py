import os
import re
import yaml
from src.models.pipeline_state import PipelineState
from src.memory.mysql_store import MySQLStore
from src.monitoring.logger import logger, set_log_context


class PHIRedactionAgent:
    def __init__(self, config: dict, mysql_store: MySQLStore):
        self.config = config or {}
        self.mysql_store = mysql_store

        # Load redaction rules
        BASE_DIR = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        RULES_PATH = os.path.join(
            BASE_DIR, "config", "phi_redaction_rules.yaml")

        self.placeholders = {
            "NAME": "[REDACTED_NAME]",
            "DATE": "[REDACTED_DATE]",
            "PHONE": "[REDACTED_PHONE]",
            "EMAIL": "[REDACTED_EMAIL]",
            "SSN": "[REDACTED_SSN]",
            "MRN": "[REDACTED_MRN]",
            "ZIP": "[REDACTED_ZIP]"
        }
        self.patterns = {}
        self.indicators = []

        if os.path.exists(RULES_PATH):
            try:
                with open(RULES_PATH, "r") as f:
                    rules = yaml.safe_load(f)
                    self.placeholders = rules.get(
                        "redaction_placeholders", self.placeholders)
                    raw_patterns = rules.get("patterns", {})
                    for k, p in raw_patterns.items():
                        self.patterns[k.upper()] = re.compile(p)
                    self.indicators = rules.get("name_context_indicators", [])
            except Exception as e:
                logger.error(f"Failed to load PHI rules: {e}")

        # Build Name detection regex based on indicators
        if self.indicators:
            # Matches indicator followed by one or two capitalized names
            pattern_str = r'\b(?:' + '|'.join(re.escape(ind)
                                              for ind in self.indicators) + r')\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\b'
            self.name_regex = re.compile(pattern_str)
        else:
            self.name_regex = re.compile(
                r'\b(?:Dr\.|Mr\.|Mrs\.|Ms\.|Patient)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\b')

    def process(self, state: PipelineState) -> PipelineState:
        """
        Scans clinical text, replaces HIPAA PHI elements with placeholders,
        and logs audit records to the database.
        """
        set_log_context(state.session_id, "phi_redaction_agent")
        logger.info(
            f"Scanning document {state.document_id} for PHI compliance")

        text = state.text
        redactions = []

        # 1. Find standard regex matches (SSN, Phone, Email, MRN, ZIP)
        for phi_type, regex in self.patterns.items():
            for match in regex.finditer(text):
                redactions.append({
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(),
                    "type": phi_type,
                    "placeholder": self.placeholders.get(phi_type, f"[REDACTED_{phi_type}]")
                })

        # 2. Find Patient/Physician Names using context heuristics
        for match in self.name_regex.finditer(text):
            # The name is in capture group 1
            name_text = match.group(1)
            name_start = match.start(1)
            name_end = match.end(1)
            redactions.append({
                "start": name_start,
                "end": name_end,
                "text": name_text,
                "type": "NAME",
                "placeholder": self.placeholders.get("NAME", "[REDACTED_NAME]")
            })

        # 3. Find Dates (except years which are allowed in HIPAA Safe Harbor if under 89yo)
        # Matches formats: MM/DD/YYYY, YYYY-MM-DD, month words followed by day/year
        date_regex = re.compile(
            r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})|(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\b', re.IGNORECASE)
        for match in date_regex.finditer(text):
            redactions.append({
                "start": match.start(),
                "end": match.end(),
                "text": match.group(),
                "type": "DATE",
                "placeholder": self.placeholders.get("DATE", "[REDACTED_DATE]")
            })

        if not redactions:
            logger.info("No PHI elements detected.")
            state.current_stage = "EXTRACTION"
            return state

        # Sort redactions from end to start to prevent offset shifts
        redactions.sort(key=lambda x: x["start"], reverse=True)

        # Deduplicate overlapping matches
        cleaned_redactions = []
        last_start = len(text) + 1
        for red in redactions:
            if red["end"] <= last_start:
                cleaned_redactions.append(red)
                last_start = red["start"]

        # Perform replacements and log in DB
        for red in cleaned_redactions:
            original = red["text"]
            redacted = red["placeholder"]
            start = red["start"]
            end = red["end"]

            # Apply to text
            text = text[:start] + redacted + text[end:]

            # Audit log database entry
            try:
                self.mysql_store.log_phi_redaction(
                    session_id=state.session_id,
                    field_type=red["type"],
                    original_value=original,
                    redacted_value=redacted
                )
            except Exception as e:
                logger.error(f"Failed to log PHI redaction audit to DB: {e}")

        state.text = text
        state.current_stage = "EXTRACTION"

        logger.info(
            f"Redaction complete. Masked {len(cleaned_redactions)} PHI fields.")
        return state
