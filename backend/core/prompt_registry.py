"""
backend/core/prompt_registry.py

Version-controlled prompt template registry for clinical NLP LLM agents.
Provides template rendering, version tracking, and audit stamping.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_CLINICAL_PROMPT_V2 = """You are a clinical NLP assistant. Analyze the clinical note and return a JSON object with extracted medical entities:
Clinical Note: "{clinical_note}"
Return ONLY valid JSON matching this schema:
{{
  "diseases": ["name"],
  "symptoms": ["name"],
  "drugs": ["name"],
  "dosages": ["dose"]
}}"""

class PromptRegistry:
    """
    Version-controlled prompt loader.
    """
    _prompts: Dict[str, Dict[str, Any]] = {
        "clinical_ner_v2.1": {
            "version": "v2.1",
            "template": DEFAULT_CLINICAL_PROMPT_V2,
            "created_at": "2026-07-30T00:00:00Z"
        }
    }

    @classmethod
    def get_prompt(cls, prompt_key: str = "clinical_ner_v2.1") -> Dict[str, Any]:
        return cls._prompts.get(prompt_key, cls._prompts["clinical_ner_v2.1"])

    @classmethod
    def render(cls, prompt_key: str, **kwargs) -> str:
        prompt_data = cls.get_prompt(prompt_key)
        template = prompt_data["template"]
        return template.format(**kwargs)
