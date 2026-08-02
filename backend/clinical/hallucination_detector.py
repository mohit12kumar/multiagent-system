"""
backend/clinical/hallucination_detector.py

AI Safety Guardrails: Clinical Contradiction Guardrail & Hallucination Detector.
Interprets physiological/demographic compatibility and verifies factual grounding against source text.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.core.exceptions import ClinicalRuleError

logger = logging.getLogger(__name__)


class ClinicalContradictionGuardrail:
    """
    Dedicated pre-flight safety check evaluating physiological and demographic feasibility.
    """

    IMPOSSIBLE_DEMOGRAPHIC_COMBINATIONS = [
        {"gender": "male", "condition": "pregnancy", "action": "REJECT"},
        {"gender": "male", "condition": "pregnant", "action": "REJECT"},
        {"gender": "male", "medication": "prenatal vitamins", "action": "FLAG"},
        {"gender": "female", "condition": "prostate cancer", "action": "REJECT"},
    ]

    INCOMPATIBLE_ROUTES = [
        {"medication": "metformin", "route": "inhalation", "action": "REJECT"},
        {"medication": "metformin", "route": "inhaler", "action": "REJECT"},
        {"medication": "salbutamol", "route": "iv push", "action": "FLAG"},
        {"medication": "albuterol", "route": "iv push", "action": "FLAG"},
        {"medication": "paracetamol", "route": "epidural", "action": "REJECT"},
        {"medication": "insulin", "route": "inhalation", "action": "FLAG"},
    ]

    def evaluate_contradictions(
        self,
        patient_demographics: Dict[str, Any],
        clinical_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluates patient gender, conditions, and medications against clinical contradiction rules.
        Returns a list of detected contradiction violations.
        """
        violations = []
        gender = str(patient_demographics.get("gender", "")).strip().lower()
        conditions = [str(c).strip().lower() for c in clinical_data.get("conditions", [])]
        medications = clinical_data.get("medications", [])

        # 1. Demographic & Physiological Feasibility Checks
        for rule in self.IMPOSSIBLE_DEMOGRAPHIC_COMBINATIONS:
            r_gender = rule["gender"]
            if gender == r_gender:
                if "condition" in rule and any(rule["condition"] in c for c in conditions):
                    violations.append({
                        "rule_type": "DEMOGRAPHIC_CONTRADICTION",
                        "severity": rule["action"],
                        "description": f"Physiological contradiction: Gender '{gender.capitalize()}' with condition '{rule['condition']}'",
                        "field": "conditions"
                    })
                if "medication" in rule:
                    for med in medications:
                        med_name = (med.get("name") or med.get("generic_name") or str(med)).strip().lower() if isinstance(med, dict) else str(med).strip().lower()
                        if rule["medication"] in med_name:
                            violations.append({
                                "rule_type": "DEMOGRAPHIC_MED_CONTRADICTION",
                                "severity": rule["action"],
                                "description": f"Physiological contradiction: Gender '{gender.capitalize()}' with medication '{rule['medication']}'",
                                "field": "medications"
                            })

        # 2. Route & Administration Incompatibilities
        for med in medications:
            if isinstance(med, dict):
                med_name = (med.get("name") or med.get("generic_name") or "").strip().lower()
                route = (med.get("route") or "").strip().lower()

                for rule in self.INCOMPATIBLE_ROUTES:
                    if rule["medication"] in med_name and rule["route"] in route:
                        violations.append({
                            "rule_type": "ROUTE_INCOMPATIBILITY",
                            "severity": rule["action"],
                            "description": f"Impossible administration route: Medication '{med_name}' cannot be administered via '{route}'",
                            "field": "medications"
                        })

        return violations

    def enforce_preflight_checks(
        self,
        patient_demographics: Dict[str, Any],
        clinical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes preflight validation. Raises ClinicalRuleError if REJECT-level contradiction exists.
        """
        violations = self.evaluate_contradictions(patient_demographics, clinical_data)

        rejections = [v for v in violations if v["severity"] == "REJECT"]
        if rejections:
            err_msg = "; ".join([r["description"] for r in rejections])
            logger.error(f"Clinical contradiction pre-flight rejection: {err_msg}")
            raise ClinicalRuleError(f"Clinical Contradiction Intercepted: {err_msg}")

        flags = [v for v in violations if v["severity"] == "FLAG"]
        return {
            "passed": True,
            "status": "FLAGGED" if flags else "APPROVED",
            "violations": violations
        }


class HallucinationDetector:
    """
    4-Stage Guardrail engine detecting AI hallucinations and medical contradictions.
    """

    def __init__(self):
        self.guardrail = ClinicalContradictionGuardrail()

    def detect_hallucinations(
        self,
        raw_text: str,
        extracted_data: Dict[str, Any],
        patient_demographics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validates extraction grounding against source text and checks for clinical contradictions.
        """
        patient_demographics = patient_demographics or {}
        text_lower = raw_text.lower()
        hallucinated_facts = []

        # Validate medications grounding
        medications = extracted_data.get("medications", [])
        for med in medications:
            med_name = (med.get("name") or med.get("generic_name") or str(med)).strip().lower() if isinstance(med, dict) else str(med).strip().lower()
            if med_name and med_name not in text_lower:
                words = [w for w in re.split(r"\W+", med_name) if len(w) > 2]
                if not any(w in text_lower for w in words):
                    hallucinated_facts.append({
                        "fact_type": "UNGROUNDED_MEDICATION",
                        "entity": med_name,
                        "description": f"Medication '{med_name}' has no textual evidence in source note"
                    })

        contradiction_results = self.guardrail.evaluate_contradictions(patient_demographics, extracted_data)
        has_rejection = any(v["severity"] == "REJECT" for v in contradiction_results)

        hallucination_rate = len(hallucinated_facts) / max(1, len(medications))
        status = "REJECTED" if has_rejection else ("FLAGGED" if hallucinated_facts or contradiction_results else "APPROVED")

        return {
            "status": status,
            "passed": not has_rejection,
            "hallucination_rate": round(hallucination_rate, 4),
            "hallucinations": hallucinated_facts,
            "contradictions": contradiction_results,
            "grounding_confidence": max(0.0, round(1.0 - hallucination_rate, 2))
        }

    @classmethod
    def verify_extraction_output(
        cls,
        patient_text: str,
        medications: List[Dict[str, Any]],
        diseases: List[str] = None,
        patient_gender: str = "unspecified"
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Class method for backward compatibility.
        """
        instance = cls()
        data = {
            "medications": medications,
            "conditions": diseases or []
        }
        res = instance.detect_hallucinations(patient_text, data, {"gender": patient_gender})
        valid_meds = [m for m in medications if m.get("name", "").lower() not in [h["entity"] for h in res["hallucinations"]]]
        rejections = res["contradictions"] + res["hallucinations"]
        return valid_meds, rejections
