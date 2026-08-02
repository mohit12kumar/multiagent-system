"""
backend/clinical/rules_dsl.py

Declarative Clinical Rules DSL Engine.
Parses and evaluates declarative YAML/JSON clinical rules (e.g. IF egfr < 30 THEN reduce metformin),
allowing non-developer medical teams to modify decision support rules without code changes.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("multiagent_ner")

class DeclarativeRulesEngine:
    """
    Evaluates declarative JSON/YAML clinical rules against patient features.
    """

    DEFAULT_DECLARATIVE_RULES = [
        {
            "id": "RULE_RENAL_METFORMIN_30",
            "if": {"feature": "egfr", "operator": "<", "value": 30},
            "then": {"action": "REDUCE_OR_DISCONTINUE_METFORMIN", "recommendation": "Metformin is contraindicated or requires 50% dose reduction for eGFR < 30 mL/min."},
            "severity": "HIGH"
        },
        {
            "id": "RULE_HYPERKALEMIA_K_6",
            "if": {"feature": "potassium", "operator": ">=", "value": 6.0},
            "then": {"action": "DISCONTINUE_ACE_ARB_SPIRONOLACTONE", "recommendation": "Serum potassium >= 6.0 mmol/L requires withholding ACEi/ARB/Spironolactone."},
            "severity": "CRITICAL"
        },
        {
            "id": "RULE_AST_ALT_3X",
            "if": {"feature": "alt", "operator": ">=", "value": 150},
            "then": {"action": "HOLD_STATIN_THERAPY", "recommendation": "Elevated transaminases (ALT > 3x ULN) require holding statin therapy."},
            "severity": "HIGH"
        }
    ]

    def __init__(self, custom_rules: List[Dict[str, Any]] = None):
        self.rules = custom_rules or list(self.DEFAULT_DECLARATIVE_RULES)

    def evaluate_rules(self, patient_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluates declared rules against patient features.
        """
        triggered = []
        for rule in self.rules:
            cond = rule.get("if", {})
            feat = cond.get("feature")
            op = cond.get("operator")
            val = cond.get("value")

            if feat in patient_features:
                p_val = float(patient_features[feat])
                is_match = False
                if op == "<" and p_val < val: is_match = True
                elif op == "<=" and p_val <= val: is_match = True
                elif op == ">" and p_val > val: is_match = True
                elif op == ">=" and p_val >= val: is_match = True
                elif op == "==" and p_val == val: is_match = True

                if is_match:
                    res = {
                        "rule_id": rule["id"],
                        "triggered_feature": feat,
                        "observed_value": p_val,
                        "action": rule["then"]["action"],
                        "recommendation": rule["then"]["recommendation"],
                        "severity": rule.get("severity", "MEDIUM")
                    }
                    triggered.append(res)
                    logger.info(f"[RulesDSL] Triggered rule '{rule['id']}': {res['recommendation']}")

        return triggered
