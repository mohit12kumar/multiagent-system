import os
import json
from typing import Dict, Any, List

class ClinicalRuleEngine:
    """Configuration-driven Clinical Rule Engine evaluating lab/vital thresholds, contraindications, and organ risk triggers."""

    _RULES_CACHE = None

    @classmethod
    def load_rules(cls) -> Dict[str, Any]:
        if cls._RULES_CACHE is not None:
            return cls._RULES_CACHE

        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "clinical_rules.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cls._RULES_CACHE = json.load(f)
        except Exception:
            cls._RULES_CACHE = {"lab_thresholds": [], "contraindication_rules": []}
        return cls._RULES_CACHE

    @classmethod
    def evaluate_lab_thresholds(cls, labs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rules = cls.load_rules().get("lab_thresholds", [])
        alerts = []

        for l in labs:
            l_name = (l.get("lab") or l.get("name") or "").lower()
            try:
                l_val = float(str(l.get("value", "")).split()[0])
            except (ValueError, TypeError):
                continue

            for r in rules:
                if r["marker"].lower() in l_name:
                    op = r["operator"]
                    thresh = float(r["value"])
                    triggered = False
                    if op == ">" and l_val > thresh: triggered = True
                    elif op == "<" and l_val < thresh: triggered = True
                    elif op == ">=" and l_val >= thresh: triggered = True
                    elif op == "<=" and l_val <= thresh: triggered = True
                    elif op == "==" and l_val == thresh: triggered = True

                    if triggered:
                        alerts.append({
                            "marker": r["marker"],
                            "value": l_val,
                            "unit": r.get("unit", ""),
                            "severity": r["severity"],
                            "condition": r["condition"],
                            "risk": r["risk"],
                            "action": r["action"]
                        })
        return alerts
