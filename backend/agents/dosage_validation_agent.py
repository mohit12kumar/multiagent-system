"""
Dosage & Formulation Validation Agent.
Validates extracted medication dosages, units, and formulations against clinical guidelines.
Generates warnings for clinically inconsistent or non-standard dosages and formulation mismatches.
"""

from typing import Dict, Any, Tuple, Optional
from src.monitoring.logger import logger


class DosageValidationAgent:
    """Validates medication dosages and formulations against clinical reference norms."""

    # Standard clinical dosage & formulation reference database
    DOSAGE_KNOWLEDGE = {
        "azithromycin": {
            "valid_doses": ["250 mg", "500 mg", "250mg", "500mg"],
            "max_daily_mg": 500,
            "allowed_routes": ["PO (Oral)", "Oral", "IV (Intravenous)"],
            "allowed_formulations": ["Tablet", "Capsule", "Suspension", "Injection"],
            "forbidden_formulations": ["Inhaler", "Puff", "Topical"],
        },
        "omeprazole": {
            "valid_doses": ["10 mg", "20 mg", "40 mg", "10mg", "20mg", "40mg"],
            "max_daily_mg": 80,
            "allowed_routes": ["PO (Oral)", "Oral", "IV (Intravenous)"],
            "allowed_formulations": ["Capsule", "Tablet", "Injection"],
            "forbidden_formulations": ["Inhaler", "Puff"],
        },
        "salbutamol": {
            "valid_doses": ["100 mcg", "2 puffs", "1 puff", "2.5 mg", "5 mg"],
            "allowed_routes": ["Inhalation", "Oral (Liquid)"],
            "allowed_formulations": ["Inhaler", "Nebulizer Solution", "Syrup"],
            "forbidden_formulations": ["Tablet"],
        },
        "albuterol": {
            "valid_doses": ["90 mcg", "2 puffs", "1 puff", "2.5 mg"],
            "allowed_routes": ["Inhalation"],
            "allowed_formulations": ["Inhaler", "Nebulizer Solution"],
        },
        "amlodipine": {
            "valid_doses": ["2.5 mg", "5 mg", "10 mg", "2.5mg", "5mg", "10mg"],
            "max_daily_mg": 10,
            "allowed_routes": ["PO (Oral)", "Oral"],
            "allowed_formulations": ["Tablet"],
        },
        "metformin": {
            "valid_doses": ["500 mg", "850 mg", "1000 mg", "500mg", "850mg", "1000mg"],
            "max_daily_mg": 2550,
            "allowed_routes": ["PO (Oral)", "Oral"],
            "allowed_formulations": ["Tablet"],
        },
        "losartan": {
            "valid_doses": ["25 mg", "50 mg", "100 mg", "25mg", "50mg", "100mg"],
            "max_daily_mg": 100,
            "allowed_routes": ["PO (Oral)", "Oral"],
            "allowed_formulations": ["Tablet"],
        },
        "atorvastatin": {
            "valid_doses": ["10 mg", "20 mg", "40 mg", "80 mg", "10mg", "20mg", "40mg", "80mg"],
            "max_daily_mg": 80,
            "allowed_routes": ["PO (Oral)", "Oral"],
            "allowed_formulations": ["Tablet"],
        },
        "aspirin": {
            "valid_doses": ["75 mg", "81 mg", "100 mg", "325 mg", "500 mg"],
            "max_daily_mg": 4000,
            "allowed_routes": ["PO (Oral)", "Oral"],
            "allowed_formulations": ["Tablet"],
        },
    }

    @classmethod
    def validate(cls, med_name: str, dosage: Optional[str], route: Optional[str], formulation: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates dosage and formulation for a medication entity.
        Returns: (is_valid: bool, clinical_warning: Optional[str])
        """
        if not med_name:
            return True, None

        m_low = med_name.strip().lower()
        d_str = (dosage or "").strip().lower()
        r_str = (route or "").strip().lower()
        f_str = (formulation or "").strip().lower()

        # Find knowledge record
        ref = None
        for k, v in cls.DOSAGE_KNOWLEDGE.items():
            if k in m_low:
                ref = v
                break

        if not ref:
            return True, None

        warnings = []

        # 1. Formulation mismatch check
        if "forbidden_formulations" in ref:
            for forb in ref["forbidden_formulations"]:
                if forb.lower() in f_str or forb.lower() in d_str:
                    warnings.append(f"Incompatible formulation '{formulation or dosage}' for {med_name.title()}; expected {', '.join(ref.get('allowed_formulations', ['Oral']))}.")

        # 2. Dosage check
        if d_str and d_str != "n/a" and d_str != "as prescribed":
            valid_doses = [x.lower() for x in ref.get("valid_doses", [])]
            if valid_doses and not any(vd in d_str for vd in valid_doses):
                # Try extracting numerical mg
                import re
                m_num = re.search(r'(\d+(?:\.\d+)?)\s*mg', d_str)
                if m_num and "max_daily_mg" in ref:
                    val_mg = float(m_num.group(1))
                    if val_mg > ref["max_daily_mg"]:
                        warnings.append(f"High dose {dosage} for {med_name.title()} exceeds recommended max dose ({ref['max_daily_mg']} mg/day).")
                    else:
                        warnings.append(f"Non-standard dose {dosage} for {med_name.title()}; standard doses: {', '.join(ref['valid_doses'])}.")

        # 3. Route check
        if r_str and "allowed_routes" in ref:
            allowed = [ar.lower() for ar in ref["allowed_routes"]]
            if not any(al in r_str for al in allowed):
                warnings.append(f"Route '{route}' may be incompatible with {med_name.title()} (typical route: {ref['allowed_routes'][0]}).")

        if warnings:
            joined_warn = " | ".join(warnings)
            logger.warning(f"DosageValidationAgent warning for {med_name}: {joined_warn}")
            return False, joined_warn

        return True, None
