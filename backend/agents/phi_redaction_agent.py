import re
from typing import Dict, Any, List
from backend.models.pipeline_state import PipelineState
from src.monitoring.logger import logger


class PHIRedactionAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def process(self, state: PipelineState) -> PipelineState:
        logger.info(f"Executing PHI Redaction Agent for session {state.session_id}")
        text = state.text
        state.original_text = text

        phi_audits = []

        # 1. Names: Patient [Name], Mr. [Name], Mrs. [Name]
        name_patterns = [
            (r'(?i)\b(patient|mr\.|mrs\.|ms\.|dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', "[REDACTED NAME]"),
            (r'(?i)\bName:\s*([A-Za-z\s]+)(?=\n|,|\.)', "Name: [REDACTED NAME]")
        ]

        # 2. DOB & Dates: DOB: MM/DD/YYYY, DD-MM-YYYY
        dob_patterns = [
            (r'(?i)\b(DOB|Date of Birth):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', r'\1: [REDACTED DOB]'),
            (r'\b(0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])[/-](19|20)\d{2}\b', '[REDACTED DATE]')
        ]

        # 3. Phone numbers: (123) 456-7890 or 123-456-7890
        phone_patterns = [
            (r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[REDACTED PHONE]')
        ]

        # 4. SSN & Hospital IDs: ID: 12345, SSN: 123-45-6789
        id_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED SSN]'),
            (r'(?i)\b(MRN|ID|Hospital ID|Patient ID):\s*([A-Za-z0-9-]+)', r'\1: [REDACTED ID]')
        ]

        # Apply replacements
        for pat, repl in name_patterns + dob_patterns + phone_patterns + id_patterns:
            matches = list(re.finditer(pat, text))
            for match in matches:
                phi_audits.append({
                    "entity_type": "PHI",
                    "original": match.group(0),
                    "redacted": repl
                })
            text = re.sub(pat, repl, text)

        state.text = text
        state.phi_redactions = phi_audits
        logger.info(f"PHI Redaction Agent complete. Redacted {len(phi_audits)} items.")
        return state
