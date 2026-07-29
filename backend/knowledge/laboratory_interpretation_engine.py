import re
from typing import Dict, Any, List, Optional
from backend.knowledge.knowledge_loader import KnowledgeLoader

class LaboratoryInterpretationEngine:
    """
    LOINC-Driven Laboratory Test Interpretation Engine.
    Evaluates raw lab text or values against LOINC reference ranges, critical value thresholds,
    and associated disease linkages.
    """

    def __init__(self, loader: Optional[KnowledgeLoader] = None):
        self.loader = loader or KnowledgeLoader()

    def evaluate_lab_value(self, test_name: str, value: float) -> Dict[str, Any]:
        concept = self.loader.get_lab(test_name)
        if not concept:
            return {
                "test_name": test_name,
                "value": value,
                "interpretation": "Normal",
                "severity": "Normal",
                "associated_diseases": []
            }

        ref = concept.get("reference_range", {})
        crit = concept.get("critical_values", {})
        interp_msgs = concept.get("interpretations", {})

        norm_min = ref.get("normal_min", 0.0)
        norm_max = ref.get("normal_max", 9999.0)

        crit_low = crit.get("critical_low", -9999.0)
        crit_high = crit.get("critical_high", 9999.0)

        severity = "Normal"
        interpretation = interp_msgs.get("normal", "Normal Range")

        if value <= crit_low:
            severity = "Critical"
            interpretation = f"CRITICAL LOW: {interp_msgs.get('low', 'Severe Hypo-value')}"
        elif value >= crit_high:
            severity = "Critical"
            interpretation = f"CRITICAL HIGH: {interp_msgs.get('high', 'Severe Hyper-value')}"
        elif value < norm_min:
            severity = "Elevated" if "Low" not in interp_msgs.get("low", "") else "Low"
            interpretation = interp_msgs.get("low", "Below Normal Reference Range")
        elif value > norm_max:
            severity = "Elevated"
            interpretation = interp_msgs.get("high", "Above Normal Reference Range")

        return {
            "test_name": concept.get("test_name"),
            "loinc_code": concept.get("loinc_code"),
            "value": value,
            "unit": concept.get("unit"),
            "interpretation": interpretation,
            "severity": severity,
            "associated_diseases": concept.get("associated_diseases", []),
            "monitoring_recommendations": concept.get("monitoring_recommendations")
        }
