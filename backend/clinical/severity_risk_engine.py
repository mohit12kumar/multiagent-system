from typing import Dict, Any, List, Tuple

class SeverityRiskEngine:
    """Classifies condition severity, predicts complication risks, and computes smart doctor triage priority."""

    # Rule-based complication prediction map
    RISK_PREDICTION_MAP = {
        "hypertension": ["Stroke", "Heart Failure", "Kidney Failure", "Coronary Artery Disease"],
        "essential hypertension": ["Stroke", "Heart Failure", "Kidney Failure"],
        "pneumonia": ["Sepsis", "Respiratory Failure", "Pleural Effusion", "Acute Respiratory Distress Syndrome"],
        "community acquired pneumonia": ["Sepsis", "Respiratory Failure", "Empyema"],
        "diabetes": ["Diabetic Nephropathy", "Retinopathy", "Peripheral Neuropathy", "Cardiovascular Disease"],
        "diabetes mellitus": ["Diabetic Nephropathy", "Retinopathy", "Peripheral Neuropathy"],
        "chronic kidney disease": ["End-Stage Renal Disease", "Severe Anemia", "Hyperkalemia"],
        "asthma": ["Status Asthmaticus", "Respiratory Arrest", "Pneumothorax"],
        "copd": ["Acute COPD Exacerbation", "Cor Pulmonale", "Respiratory Failure"],
        "myocardial infarction": ["Cardiogenic Shock", "Ventricular Arrhythmia", "Heart Failure"]
    }

    @classmethod
    def evaluate_severity(cls, disease_name: str, symptoms: List[str], vitals: List[Any], labs: List[Any]) -> Tuple[str, str]:
        """Returns (Severity Level: Mild/Moderate/Severe/Critical, Reason)."""
        d_lower = disease_name.lower()
        s_count = len(symptoms)

        # High-risk vitals check
        high_bp = any("180" in str(v) or "110" in str(v) or "crisis" in str(v).lower() for v in vitals)
        high_fever = any("103" in str(v) or "104" in str(v) for v in vitals) or any("high fever" in str(s).lower() for s in symptoms)

        if "pneumonia" in d_lower:
            if "breathlessness" in symptoms or "shortness of breath" in symptoms or high_fever:
                return "Severe", "Productive cough, high fever, and dyspnea indicate severe pulmonary involvement."
            return "Moderate", "Localized pulmonary infection requiring outpatient antimicrobial management."

        if "hypertension" in d_lower or "htn" in d_lower:
            if high_bp:
                return "Critical (Hypertensive Crisis)", "Blood pressure >180/110 mmHg indicates hypertensive crisis risk."
            if any("140" in str(v) or "150" in str(v) or "160" in str(v) for v in vitals) or s_count >= 1:
                return "Stage 2 (Poorly Controlled)", "Stage 2 Hypertension with documented elevated blood pressure and multi-drug therapy."
            return "Stage 1 (Elevated)", "Elevated blood pressure managed with routine anti-hypertensive therapy."

        if "diabetes" in d_lower:
            if any("hba1c" in str(l).lower() and ("8." in str(l) or "9." in str(l) or "10." in str(l)) for l in labs):
                return "Poor Glycemic Control", "HbA1c elevated >8.0% indicating poor glycemic control."
            return "Moderate (Managed)", "Chronic glycemic management requiring regular HbA1c monitoring."

        if "hyperlipidemia" in d_lower or "lipid" in d_lower:
            return "Severe Dyslipidemia (High CV Risk)", "Elevated LDL (>160 mg/dL) and reduced HDL with elevated cardiovascular risk."

        if "myocardial infarction" in d_lower or "acute mi" in d_lower or "stemi" in d_lower:
            return "Critical (Acute STEMI)", "Elevated troponin and acute myocardial injury indicate high risk of cardiogenic shock."

        if "hyperkalemia" in d_lower:
            return "Critical (Potassium >6.0 mmol/L)", "Serum potassium >6.0 mmol/L indicates severe hyperkalemia with arrhythmia risk."

        if "pulmonary edema" in d_lower:
            return "Critical (Acute Pulmonary Edema)", "Alveolar fluid overload and severe dyspnea require immediate diuresis."

        if "heart failure" in d_lower or "chf" in d_lower:
            return "Severe (EF 30% / Elevated BNP)", "Elevated BNP (>1000 pg/mL) and reduced EF indicate acute-on-chronic heart failure."

        if "kidney" in d_lower or "ckd" in d_lower:
            return "Stage IV (Severe Renal Impairment)", "Renal impairment requiring nephrology consultation."

        if s_count >= 3:
            return "Severe", "Multiple severe clinical findings detected."
        elif s_count >= 1:
            return "Moderate", "Standard clinical presentation requiring monitoring."
        return "Mild", "Asymptomatic or mild presentation."

    @classmethod
    def predict_risks(cls, disease_name: str) -> List[str]:
        d_lower = disease_name.lower()
        for k, risks in cls.RISK_PREDICTION_MAP.items():
            if k in d_lower or d_lower in k:
                return risks
        return ["Disease Progression", "Secondary Infection", "Treatment Resistance"]

    @classmethod
    def compute_doctor_triage_priority(cls, severity: str, overall_confidence: float, risks: List[str]) -> Dict[str, Any]:
        """Calculates smart doctor review triage level (Critical 15m, High 1h, Medium 24h, Routine)."""
        if severity == "Critical" or "Sepsis" in risks or "Stroke" in risks:
            return {
                "level": "Critical",
                "badge": "Critical ⚡ 15 min",
                "max_review_time": "15 minutes",
                "priority_score": 95
            }
        elif severity == "Severe" or overall_confidence < 0.75:
            return {
                "level": "High",
                "badge": "High 🚨 1 hour",
                "max_review_time": "1 hour",
                "priority_score": 80
            }
        elif severity == "Moderate":
            return {
                "level": "Medium",
                "badge": "Medium 🟡 24 hours",
                "max_review_time": "24 hours",
                "priority_score": 50
            }
        return {
            "level": "Low",
            "badge": "Routine 🟢 Standard",
            "max_review_time": "Routine",
            "priority_score": 20
        }

    @classmethod
    def compute_organ_risk_stratification(cls, diseases: List[str], labs: List[Any], vitals: List[Any]) -> Dict[str, str]:
        """Calculates multi-organ risk stratification (Stroke, Cardiac, Renal Failure, Respiratory Failure, Overall)."""
        dis_str = " ".join(diseases).lower()
        lab_str = " ".join([str(l) for l in labs]).lower()
        vital_str = " ".join([str(v) for v in vitals]).lower()

        stroke_risk = "High" if "hypertension" in dis_str or "160" in vital_str or "stroke" in dis_str or "cad" in dis_str else "Moderate"
        cardiac_risk = "Very High" if "infarction" in dis_str or "heart failure" in dis_str or "chf" in dis_str or "troponin" in lab_str or "bnp" in lab_str else "High"
        renal_risk = "Very High" if "creatinine" in lab_str or "egfr" in lab_str or "potassium" in lab_str or "ckd" in dis_str or "hyperkalemia" in dis_str else "Moderate"
        resp_risk = "Moderate" if "edema" in dis_str or "pneumonia" in dis_str or "copd" in dis_str else "Low"
        overall_risk = "Critical" if "infarction" in dis_str or "hyperkalemia" in dis_str or "edema" in dis_str else ("High" if "ckd" in dis_str else "Moderate")

        return {
            "stroke_risk": stroke_risk,
            "cardiac_risk": cardiac_risk,
            "renal_failure_risk": renal_risk,
            "respiratory_failure_risk": resp_risk,
            "overall_risk_level": overall_risk
        }
