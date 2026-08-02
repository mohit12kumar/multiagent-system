"""
backend/clinical/therapeutic_duplication_engine.py

Therapeutic Duplication Detection Engine.
Identifies duplicate therapy in the same drug class (e.g., dual NSAIDs, dual ACE/ARBs, dual Statins)
to prevent adverse pharmacological overlap.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("multiagent_ner")

# Drug Class Mapping
_DRUG_CLASSES: Dict[str, List[str]] = {
    "NSAIDs": ["ibuprofen", "diclofenac", "naproxen", "aceclofenac", "meftal", "indomethacin", "meloxicam", "piroxicam"],
    "Statins": ["atorvastatin", "rosuvastatin", "simvastatin", "pravastatin", "lovastatin"],
    "ACE_Inhibitors": ["ramipril", "lisinopril", "enalapril", "perindopril", "captopril"],
    "ARBs": ["telmisartan", "losartan", "valsartan", "candesartan", "irbesartan"],
    "Biguanides": ["metformin", "glucophage"],
    "DHP_CCBs": ["amlodipine", "nifedipine", "felodipine"],
    "Inhaled_Beta_Agonists": ["salbutamol", "albuterol", "levosalbutamol", "formoterol", "salmeterol"]
}

class TherapeuticDuplicationEngine:
    """
    Detects therapeutic duplication across prescribed medication regimens.
    """

    @classmethod
    def detect_duplications(cls, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scans a list of medication dictionaries for duplicate drug classes.
        """
        class_matches: Dict[str, List[str]] = {}
        for m in medications:
            name = (m.get("name") or m.get("generic_name") or "").lower().strip()
            for cls_name, drug_list in _DRUG_CLASSES.items():
                if any(d in name for d in drug_list):
                    class_matches.setdefault(cls_name, []).append(m.get("name", name.title()))

        warnings = []
        for cls_name, matched_drugs in class_matches.items():
            if len(matched_drugs) > 1:
                warn = {
                    "drug_class": cls_name,
                    "conflicting_drugs": matched_drugs,
                    "severity": "HIGH_THERAPEUTIC_DUPLICATION",
                    "message": f"Therapeutic duplication detected in drug class '{cls_name}': {', '.join(matched_drugs)}."
                }
                warnings.append(warn)
                logger.warning(f"[TherapeuticDuplication] {warn['message']}")

        return warnings
