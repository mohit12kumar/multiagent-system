from backend.disease_plugins.base_plugin import BaseDiseasePlugin
from typing import Dict, Any, List

class CKDPlugin(BaseDiseasePlugin):
    @property
    def disease_name(self) -> str:
        return "Chronic Kidney Disease"

    @property
    def icd10_code(self) -> str:
        return "N18.30"

    @property
    def snomed_code(self) -> str:
        return "709044004"

    def calculate_severity(self, symptoms: List[str], labs: List[Any], vitals: List[Any]) -> str:
        egfr = self._extract_egfr(labs)
        if egfr is not None:
            if egfr < 15:
                return "Kidney Failure / Critical"
            elif egfr <= 29:
                return "Severe"
            elif egfr <= 59:
                return "Moderate"
            elif egfr <= 89:
                return "Mild"
        return "Severe"

    def calculate_stage(self, labs: List[Any], vitals: List[Any]) -> str:
        egfr = self._extract_egfr(labs)
        if egfr is not None:
            if egfr >= 90:
                return "Stage 1 (90-100% kidney function)"
            elif egfr >= 60:
                return "Stage 2 (89-60% kidney function)"
            elif egfr >= 45:
                return "Stage 3a (59-45% kidney function)"
            elif egfr >= 30:
                return "Stage 3b (44-30% kidney function)"
            elif egfr >= 15:
                return "Stage 4 (29-15% kidney function)"
            else:
                return "Stage 5 (<15% kidney function - Failure)"
        return "Stage 4 (29-15% kidney function)"

    def _extract_egfr(self, labs: List[Any]) -> float | None:
        for item in labs:
            if isinstance(item, dict):
                name = str(item.get("lab", item.get("name", ""))).lower()
                val = item.get("value", item.get("val"))
                if "egfr" in name and val is not None:
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        pass
        return None

    def get_guidelines(self) -> List[Dict[str, Any]]:
        return [
            {"organization": "KDIGO", "year": "2023", "class": "Class I", "level": "Level A", "recommendation": "Monitor eGFR and urine albumin-to-creatinine ratio annually"},
            {"organization": "KDIGO", "year": "2023", "class": "Class I", "level": "Level A", "recommendation": "Avoid NSAIDs in CKD Stage 3b-5 (eGFR < 45 mL/min/1.73m2)"}
        ]
