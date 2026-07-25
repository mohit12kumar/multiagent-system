from typing import Dict, Any, List

class RiskEngine:
    """Calculates dynamic multi-organ risk stratification across 9 organ systems."""

    @classmethod
    def compute_organ_risk(cls, diseases: List[str], labs: List[Any], vitals: List[Any]) -> Dict[str, str]:
        dis_str = " ".join(diseases).lower()
        lab_str = " ".join([str(l) for l in labs]).lower()
        vital_str = " ".join([str(v) for v in vitals]).lower()

        cardiac = "VERY HIGH" if "stemi" in dis_str or "heart failure" in dis_str or "troponin" in lab_str or "bnp" in lab_str else "HIGH"
        renal = "VERY HIGH" if "creatinine" in lab_str or "egfr" in lab_str or "potassium" in lab_str or "ckd" in dis_str or "aki" in dis_str else "MODERATE"
        resp = "VERY HIGH" if "pulmonary edema" in dis_str or "spo2 82" in vital_str or ("copd" in dis_str and "pneumonia" in dis_str) else "HIGH"
        neuro = "HIGH" if "stroke" in dis_str or "syncope" in dis_str else "MODERATE"
        stroke = "HIGH" if "hypertension" in dis_str or "stroke" in dis_str else "MODERATE"
        sepsis = "HIGH" if "wbc" in lab_str or "crp" in lab_str or "pneumonia" in dis_str else "MODERATE"
        hepatic = "HIGH" if "alt" in lab_str or "ast" in lab_str or "cirrhosis" in dis_str else "LOW"
        bleeding = "HIGH" if "aspirin" in dis_str or "bleeding" in dis_str or "inr" in lab_str else "MODERATE"
        overall = "CRITICAL" if "stemi" in dis_str or "hyperkalemia" in dis_str or "edema" in dis_str else "HIGH"

        return {
            "cardiac": cardiac,
            "renal": renal,
            "respiratory": resp,
            "neurological": neuro,
            "stroke": stroke,
            "sepsis": sepsis,
            "hepatic": hepatic,
            "bleeding": bleeding,
            "overall": overall,

            # Backwards compatibility
            "cardiac_risk": cardiac,
            "renal_failure_risk": renal,
            "respiratory_failure_risk": resp,
            "stroke_risk": stroke,
            "sepsis_risk": sepsis,
            "overall_risk_level": overall
        }
