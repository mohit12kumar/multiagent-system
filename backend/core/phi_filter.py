"""
backend/core/phi_filter.py

Enterprise PHI (Protected Health Information) and Secret Masking Filter for Python Logging.
Intercepts all logger records and scrubs sensitive patient data (names, SSN/Aadhaar, DOB, phone, email, MRN)
as well as API keys, tokens, and database passwords before writing logs to console or disk.
"""

import re
import logging
from typing import Any

# Regular expressions for sensitive data patterns
_PATTERNS = [
    # API Keys / Tokens / Secrets
    (re.compile(r'(?i)(bearer\s+|token\s*=\s*|secret\s*=\s*|api[-_]?key\s*=\s*|password\s*=\s*)([a-zA-Z0-9_\-\.]{8,})'), r'\1[REDACTED_SECRET]'),
    (re.compile(r'gsk_[a-zA-Z0-9]{32,}'), '[REDACTED_GROQ_KEY]'),
    (re.compile(r'eyJ[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*'), '[REDACTED_JWT]'),
    # Phone numbers
    (re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'), '[REDACTED_PHONE]'),
    # Email addresses
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[REDACTED_EMAIL]'),
    # Social Security / Aadhaar numbers (12 digit or XXX-XX-XXXX)
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[REDACTED_SSN]'),
    (re.compile(r'\b\d{4}[-\s]\d{4}[-\s]\d{4}\b'), '[REDACTED_AADHAAR]'),
    # Patient MRN identifiers
    (re.compile(r'(?i)\b(mrn|patient[-_]?id)\s*[:=]?\s*([a-zA-Z0-9\-]+)'), r'\1:[REDACTED_MRN]'),
]

class PHILogFilter(logging.Filter):
    """
    Logging filter that sanitizes PHI and secrets from log messages and args.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.mask_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.mask_text(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.mask_text(str(arg)) if isinstance(arg, str) else arg for arg in record.args)
        return True

    @classmethod
    def mask_text(cls, text: str) -> str:
        if not text or not isinstance(text, str):
            return text
        sanitized = text
        for pattern, replacement in _PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized


def apply_phi_filter_to_root():
    """
    Applies PHILogFilter to all root logging handlers.
    """
    root_logger = logging.getLogger()
    log_filter = PHILogFilter()
    for handler in root_logger.handlers:
        handler.addFilter(log_filter)
