import os
import json
from typing import Dict, Any, List

class ClinicalPathwayEngine:
    """Enterprise Clinical Pathway Engine v7.1 — Configuration-driven care pathway protocol generator."""

    _PATHWAYS_CACHE = None

    @classmethod
    def load_pathways(cls) -> Dict[str, Any]:
        if cls._PATHWAYS_CACHE:
            return cls._PATHWAYS_CACHE

        pathway_dir = os.path.join(os.path.dirname(__file__), "..", "config", "pathways")
        card_file = os.path.join(pathway_dir, "cardiology.json")
        if os.path.exists(card_file):
            try:
                with open(card_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cls._PATHWAYS_CACHE = data.get("pathways", {})
                    return cls._PATHWAYS_CACHE
            except Exception:
                pass
        return {}

    @classmethod
    def get_pathway_for_disease(cls, disease_name: str) -> List[Dict[str, str]]:
        pathways = cls.load_pathways()
        d_low = disease_name.lower().strip()

        for k, steps in pathways.items():
            if k.lower() in d_low or d_low in k.lower():
                return steps

        return [
            {"timeframe": "0 min", "step": "Initial Assessment", "action": f"Clinical Evaluation for {disease_name}"},
            {"timeframe": "60 min", "step": "Diagnostic Testing", "action": "Laboratory and Diagnostic Imaging Workup"},
            {"timeframe": "24 hours", "step": "Treatment Optimization", "action": "Guideline-Directed Medical Therapy"},
            {"timeframe": "Discharge", "step": "Follow-Up Planning", "action": "Outpatient Clinic Follow-Up"}
        ]
