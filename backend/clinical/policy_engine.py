"""
backend/clinical/policy_engine.py

Enterprise Hierarchical Policy Engine.
Cascades policy overrides from Hospital (Default) -> Department -> Doctor -> User Role.
"""

import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Evaluates policy configuration across corporate, departmental, physician, and role tiers.
    """

    DEFAULT_HOSPITAL_POLICY = {
        "min_confidence": 0.70,
        "escalate_low_egfr": False,
        "require_dual_signoff_for_narcotics": True,
        "strict_dose_cap_enforcement": True,
        "allow_off_label_guideline": False,
        "max_daily_morphine_milligram_equivalent": 90.0,
    }

    def __init__(self):
        self.hospital_policy = dict(self.DEFAULT_HOSPITAL_POLICY)
        self.department_policies: Dict[str, Dict[str, Any]] = {
            "nephrology": {
                "min_confidence": 0.80,
                "escalate_low_egfr": True,
                "strict_renol_dosing": True,
            },
            "cardiology": {
                "min_confidence": 0.75,
                "escalate_qt_prolongation": True,
            },
            "oncology": {
                "min_confidence": 0.65,
                "allow_off_label_guideline": True,
            }
        }
        self.doctor_policies: Dict[str, Dict[str, Any]] = {}
        self.role_policies: Dict[str, Dict[str, Any]] = {
            "attending_physician": {
                "allow_override": True,
            },
            "resident": {
                "require_supervisor_cosign": True,
            }
        }

    def register_department_policy(self, dept_name: str, policy: Dict[str, Any]):
        """Registers department-level policy overrides."""
        self.department_policies[dept_name.lower()] = policy

    def register_doctor_policy(self, doctor_id: str, policy: Dict[str, Any]):
        """Registers doctor-specific policy overrides."""
        self.doctor_policies[doctor_id.lower()] = policy

    def resolve_effective_policy(
        self,
        department: Optional[str] = None,
        doctor_id: Optional[str] = None,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates effective policy by cascading parameters:
        Hospital (Base) -> Department Overrides -> Doctor Overrides -> Role Overrides.
        """
        effective = dict(self.hospital_policy)

        # 1. Apply Department Tier
        if department:
            dept_key = department.strip().lower()
            if dept_key in self.department_policies:
                effective.update(self.department_policies[dept_key])

        # 2. Apply Doctor Tier
        if doctor_id:
            doc_key = doctor_id.strip().lower()
            if doc_key in self.doctor_policies:
                effective.update(self.doctor_policies[doc_key])

        # 3. Apply User Role Tier
        if role:
            role_key = role.strip().lower()
            if role_key in self.role_policies:
                effective.update(self.role_policies[role_key])

        effective["resolved_context"] = {
            "department": department,
            "doctor_id": doctor_id,
            "role": role
        }
        return effective

    def evaluate_action_permitted(
        self,
        action: str,
        confidence: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Evaluates whether a clinical AI decision passes resolved policy limits.
        """
        context = context or {}
        policy = self.resolve_effective_policy(
            department=context.get("department"),
            doctor_id=context.get("doctor_id"),
            role=context.get("role")
        )

        min_conf = policy.get("min_confidence", 0.70)
        if confidence < min_conf:
            return False, f"Action '{action}' confidence {confidence:.2f} below required policy threshold {min_conf:.2f}"

        return True, "Permitted"
