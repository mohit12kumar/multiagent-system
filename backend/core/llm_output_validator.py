"""
backend/core/llm_output_validator.py

Validates LLM-generated JSON responses for schema correctness, hallucination prevention,
and clinical sanity before entities are merged into the pipeline state.
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Terms that LLMs often hallucinate or confuse with real entities
_LLM_HALLUCINATION_BLOCKLIST = {
    "patient", "doctor", "hospital", "clinic", "treatment", "day", "days",
    "note", "report", "the", "and", "illness", "conditions", "findings",
    "mg", "tablet", "tablets", "capsule", "dose", "daily", "oral", "po"
}

def sanitize_entity_text(text: str) -> str:
    if not text:
        return ""
    # Strip control chars, trim whitespace
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text).strip()
    return cleaned[:200]

def validate_llm_json_response(raw_data: Any) -> Dict[str, List[str]]:
    """
    Validates and cleans LLM-extracted entities dict.
    Must return dict with keys: 'diseases', 'symptoms', 'drugs', 'dosages'.
    """
    result = {
        "diseases": [],
        "symptoms": [],
        "drugs": [],
        "dosages": []
    }

    if not isinstance(raw_data, dict):
        logger.warning("[LLM Validator] Expected dict output from LLM, got invalid type.")
        return result

    for key in result.keys():
        items = raw_data.get(key, [])
        if isinstance(items, list):
            cleaned_list = []
            for item in items:
                if isinstance(item, str):
                    clean_item = sanitize_entity_text(item)
                    if clean_item and clean_item.lower() not in _LLM_HALLUCINATION_BLOCKLIST and len(clean_item) >= 2:
                        cleaned_list.append(clean_item)
            result[key] = cleaned_list

    return result
