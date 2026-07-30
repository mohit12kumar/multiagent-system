"""
backend/core/model_registry.py

Enterprise Model & Vocabulary Version Registry.
Maintains version tracking for AI models, prompt templates, and clinical vocabularies (ICD-10, SNOMED CT, RxNorm)
so that every pipeline result can be reproduced and audited.
"""

from typing import Dict, Any

class ModelRegistry:
    """
    Registry for model, prompt, and terminology versions.
    """
    _VERSIONS: Dict[str, str] = {
        "spacy": "en_core_web_sm (v3.7.0)",
        "scispacy": "en_core_sci_sm (v0.5.4)",
        "biobert": "dmis-lab/biobert-v1.1",
        "local_llm": "phi3:mini (Ollama)",
        "groq_llm": "llama-3.3-70b-versatile",
        "embedding_model": "all-MiniLM-L6-v2",
        "prompt_version": "v2.1",
        "icd_version": "ICD-10-CM 2024",
        "snomed_version": "SNOMED CT US Edition 2024-03",
        "rxnorm_version": "RxNorm Monthly Release 2024-05",
        "pipeline_schema": "v2.1.0",
    }

    @classmethod
    def get_version_info(cls) -> Dict[str, str]:
        return cls._VERSIONS.copy()

    @classmethod
    def update_version(cls, key: str, version_str: str):
        cls._VERSIONS[key] = version_str
