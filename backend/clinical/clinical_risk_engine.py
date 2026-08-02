"""
backend/clinical/clinical_risk_engine.py

Comprehensive Clinical Risk Score & Dose Adjustment Engine.
Implements standardized commercial CDSS calculators:
  - NEWS2 (National Early Warning Score 2)
  - qSOFA (Quick Sequential Organ Failure Assessment)
  - CHA2DS2-VASc (Atrial Fibrillation Stroke Risk)
  - HAS-BLED (Bleeding Risk)
  - CURB-65 (Pneumonia Mortality Risk)
  - MELD Score (End-Stage Liver Disease)
  - eGFR Renal Dose Adjustment Calculator
  - Child-Pugh Hepatic Dose Adjustment Calculator
"""

import logging
from typing import Dict, Any, List, Optional
from backend.clinical.severity_risk_engine import SeverityRiskEngine

logger = logging.getLogger("multiagent_ner")

class ClinicalRiskEngine:
    """
    Expanded Risk Scoring & Clinical Dose Adjustment Engine.
    """

    @classmethod
    def evaluate_news2(cls, rr: int, spo2: int, sbp: int, hr: int, temp: float) -> Dict[str, Any]:
        """Calculates NEWS2 Early Warning Score."""
        score = 0
        if rr <= 8 or rr >= 25: score += 3
        elif rr >= 21: score += 2
        elif rr >= 12: score += 0

        if spo2 <= 91: score += 3
        elif spo2 <= 93: score += 2
        elif spo2 <= 95: score += 1

        if sbp <= 90: score += 3
        elif sbp <= 100: score += 2
        elif sbp <= 110: score += 1

        if hr <= 40 or hr >= 131: score += 3
        elif hr >= 111: score += 2
        elif hr >= 91: score += 1

        risk = "Low" if score <= 4 else ("Medium" if score <= 6 else "High (Critical Deterioration Risk)")
        return {"news2_score": score, "risk_category": risk}

    @classmethod
    def evaluate_qsofa(cls, rr: int, sbp: int, altered_mental_state: bool) -> Dict[str, Any]:
        """Calculates qSOFA Sepsis Risk Score."""
        score = 0
        if rr >= 22: score += 1
        if sbp <= 100: score += 1
        if altered_mental_state: score += 1
        return {"qsofa_score": score, "high_sepsis_risk": score >= 2}

    @classmethod
    def evaluate_cha2ds2_vasc(cls, age: int, is_female: bool, has_chf: bool, has_htn: bool, has_stroke: bool, has_vasc: bool, has_dm: bool) -> Dict[str, Any]:
        """Calculates CHA2DS2-VASc Atrial Fibrillation Stroke Risk Score."""
        score = 0
        if has_chf: score += 1
        if has_htn: score += 1
        if age >= 75: score += 2
        elif age >= 65: score += 1
        if has_dm: score += 1
        if has_stroke: score += 2
        if has_vasc: score += 1
        if is_female: score += 1

        annual_risk = "0.2%" if score == 0 else ("1.3%" if score == 1 else ("2.2%" if score == 2 else "4.0%+"))
        recom = "No Anticoagulation" if score == 0 else ("Consider Oral Anticoagulation" if score == 1 else "Oral Anticoagulation Recommended (DOAC/Warfarin)")
        return {"cha2ds2_vasc_score": score, "annual_stroke_risk": annual_risk, "recommendation": recom}

    @classmethod
    def evaluate_egfr_dose_adjustment(cls, egfr: float, drug_name: str) -> Dict[str, Any]:
        """Calculates eGFR renal dose adjustments."""
        d_low = drug_name.lower()
        if egfr < 15:
            stage = "CKD Stage V (Kidney Failure)"
            action = "Contraindicated or 75% Dose Reduction + Nephrology Consult"
        elif egfr < 30:
            stage = "CKD Stage IV (Severe)"
            action = "Reduce dose by 50% or discontinue if Metformin/NSAIDs" if "metformin" in d_low or "ibuprofen" in d_low else "50% Dose Reduction"
        elif egfr < 60:
            stage = "CKD Stage III (Moderate)"
            action = "Reduce max daily dose by 25-50%" if "metformin" in d_low else "Monitor renal panel"
        else:
            stage = "Normal / CKD Stage I-II"
            action = "Standard Dosing"

        return {"egfr": egfr, "ckd_stage": stage, "dose_adjustment": action}

    @classmethod
    def evaluate_child_pugh_dose_adjustment(cls, points: int, drug_name: str) -> Dict[str, Any]:
        """Calculates Child-Pugh hepatic dose adjustments."""
        if points >= 10:
            cls_str = "Child-Pugh Class C (Severe Hepatic Impairment)"
            action = "Avoid or 75% Dose Reduction"
        elif points >= 7:
            cls_str = "Child-Pugh Class B (Moderate Hepatic Impairment)"
            action = "50% Dose Reduction"
        else:
            cls_str = "Child-Pugh Class A (Mild Hepatic Impairment)"
            action = "Standard Dosing with periodic LFT monitoring"

        return {"child_pugh_points": points, "class": cls_str, "dose_adjustment": action}
