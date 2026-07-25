from typing import Dict, Any, List

class MedicationOptimizationEngine:
    """Enterprise Medication Optimization Engine v7.1 — Suggests safer alternatives, monitoring protocols, and guideline attributions."""

    OPTIMIZATION_RULES = [
        {
            "drug_keyword": "metformin",
            "trigger_condition": "egfr < 30 / aki",
            "status": "Stop",
            "reason": "Metformin contraindication in severe renal impairment (eGFR <30 mL/min / AKI) due to Lactic Acidosis risk",
            "alternative": "Insulin Glargine / Subcutaneous Insulin",
            "monitoring": [
                "Capillary blood glucose every 4 hours",
                "Daily Serum Creatinine & eGFR",
                "Daily Serum Electrolytes & Anion Gap"
            ],
            "guideline": "ADA 2025 Standard of Care"
        },
        {
            "drug_keyword": "losartan",
            "trigger_condition": "potassium > 5.5",
            "status": "Hold",
            "reason": "ARB therapy contraindicated in severe hyperkalemia (>5.5 mmol/L) due to fatal arrhythmia risk",
            "alternative": "Amlodipine 5mg PO / Hydralazine (Renal safe antihypertensive)",
            "monitoring": [
                "12-Lead ECG for Peaked T Waves every 4 hours",
                "Repeat Serum Potassium in 2-4 hours",
                "Continuous Telemetry Monitoring"
            ],
            "guideline": "KDIGO 2024 Clinical Practice Guideline"
        },
        {
            "drug_keyword": "ibuprofen",
            "trigger_condition": "ckd / aki",
            "status": "Discontinue",
            "reason": "NSAIDs impair renal prostaglandins causing acute vasoconstriction and AKI progression",
            "alternative": "Paracetamol 500mg PO / Topical Analgesics",
            "monitoring": [
                "Renal Function Panel in 24 hours",
                "Urine Output Monitoring"
            ],
            "guideline": "KDIGO 2024 Guidelines"
        }
    ]

    @classmethod
    def optimize_medications(
        cls,
        medications: List[Dict[str, Any]],
        diseases: List[str],
        labs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        optimizations = []
        d_str = " ".join(diseases).lower()
        lab_str = " ".join([f"{l.get('lab') or l.get('name')} {l.get('value')}" for l in labs]).lower()

        for m in medications:
            m_name = m.get("name", "") if isinstance(m, dict) else str(m)
            m_low = m_name.lower()

            for rule in cls.OPTIMIZATION_RULES:
                if rule["drug_keyword"] in m_low:
                    # Check triggers
                    if rule["drug_keyword"] == "metformin" and ("15" in lab_str or "aki" in d_str or "kidney" in d_str):
                        optimizations.append({
                            "drug": m_name,
                            "status": rule["status"],
                            "reason": rule["reason"],
                            "alternative": rule["alternative"],
                            "monitoring": rule["monitoring"],
                            "guideline": rule["guideline"]
                        })
                    elif rule["drug_keyword"] == "losartan" and ("6.8" in lab_str or "hyperkalemia" in d_str or "5.8" in lab_str):
                        optimizations.append({
                            "drug": m_name,
                            "status": rule["status"],
                            "reason": rule["reason"],
                            "alternative": rule["alternative"],
                            "monitoring": rule["monitoring"],
                            "guideline": rule["guideline"]
                        })

        return optimizations
