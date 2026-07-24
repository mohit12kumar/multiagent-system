"""
ContraindicationAgent -- Detects drug-disease, drug-lab, and drug-allergy conflicts.

Rules include Critical, Major, and Moderate severity warnings.
"""

from typing import Dict, Any, List


class ContraindicationAgent:
    """Checks for clinical contraindications and allergy conflicts."""

    RULES = [
        # (drug_keyword, condition_keyword, condition_type, severity, warning)
        # NSAIDs in renal disease
        ("ibuprofen",     "ckd",          "disease",  "Critical", "NSAIDs (Ibuprofen) are highly nephrotoxic and strictly contraindicated in CKD Stage III or worse. Discontinue immediately."),
        ("ibuprofen",     "kidney",       "disease",  "Critical", "NSAIDs (Ibuprofen) are contraindicated in renal impairment. Risk of acute-on-chronic kidney injury."),
        ("naproxen",      "kidney",       "disease",  "Critical", "NSAIDs (Naproxen) are contraindicated in renal impairment."),
        ("diclofenac",    "kidney",       "disease",  "Major",    "Diclofenac (NSAID) carries renal risk in CKD patients. Use with caution."),
        # Metformin in renal failure
        ("metformin",     "ckd",          "disease",  "Critical", "Metformin strictly contraindicated in eGFR < 30 (CKD Stage IV/V) due to high risk of fatal lactic acidosis. Hold immediately."),
        ("metphormin",    "ckd",          "disease",  "Critical", "Metformin strictly contraindicated in eGFR < 30 (CKD Stage IV/V) due to high risk of fatal lactic acidosis. Hold immediately."),
        ("metformin",     "kidney",       "disease",  "Critical", "Metformin carries severe lactic acidosis risk in renal insufficiency. Monitor eGFR."),
        # Spironolactone in hyperkalemia/renal
        ("spironolactone","hyperkalemia", "disease",  "Critical", "Spironolactone is contraindicated with hyperkalemia (K+ > 5.5 mmol/L). Risk of fatal arrhythmia."),
        ("spironolactone","kidney",       "disease",  "Major",    "Spironolactone requires extreme caution in CKD (eGFR < 30). Monitor potassium closely."),
        ("spironolactone","ckd",          "disease",  "Major",    "Spironolactone in CKD: risk of dangerous hyperkalemia. Monitor potassium every 1-2 weeks."),
        # Penicillin allergy
        ("amoxicillin",   "penicillin",   "allergy",  "Critical", "Amoxicillin is a penicillin-class antibiotic. Contraindicated in documented Penicillin allergy. Risk of anaphylaxis."),
        ("amoxycillin",   "penicillin",   "allergy",  "Critical", "Amoxycillin is contraindicated in Penicillin allergy. Switch to a macrolide or quinolone."),
        ("piperacillin",  "penicillin",   "allergy",  "Critical", "Piperacillin-Tazobactam is a penicillin-class drug. Contraindicated in Penicillin allergy."),
        # Sulfa allergy
        ("sulfamethoxazole","sulfa",      "allergy",  "Critical", "TMP-SMX (Sulfamethoxazole) is contraindicated in documented Sulfa drug allergy."),
        ("furosemide",    "sulfa",        "allergy",  "Moderate", "Furosemide has a sulfa moiety. Potential cross-reactivity with Sulfa drug allergy — use with caution."),
        # Azithromycin QT prolongation
        ("azithromycin",  "atrial fibrillation","disease","Major","Azithromycin can prolong QT interval. Use with caution in patients with pre-existing arrhythmias (Atrial Fibrillation)."),
        # Furosemide + Spironolactone (hyperkalemia when eGFR low)
        ("furosemide",    "kidney",       "disease",  "Moderate", "Furosemide in CKD: monitor electrolytes. Loop diuretics can cause volume depletion and worsening renal function."),
        # ACE/ARB in hyperkalemia
        ("lisinopril",    "hyperkalemia", "disease",  "Major",    "ACE inhibitors (Lisinopril) are relatively contraindicated with severe hyperkalemia (K+ > 5.5 mmol/L)."),
        ("losartan",      "hyperkalemia", "disease",  "Major",    "ARBs (Losartan) are relatively contraindicated with severe hyperkalemia. Monitor potassium closely."),
        # Statins in hepatic disease
        ("atorvastatin",  "hepatic",      "disease",  "Major",    "Statins (Atorvastatin) are contraindicated in active hepatic disease or unexplained elevated transaminases."),
        # Warfarin
        ("warfarin",      "bleeding",     "disease",  "Critical", "Warfarin anticoagulation carries significant bleeding risk. Monitor INR closely."),
    ]

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def check_contraindications(
        self,
        medications: List[str],
        diseases: List[str],
        allergies: List[str],
    ) -> List[Dict[str, str]]:
        """Check for contraindications across drug-disease pairs and allergy conflicts."""
        warnings: List[Dict[str, str]] = []
        meds_low    = [m.lower() for m in medications]
        dis_low     = [d.lower() for d in diseases]
        allergy_low = [a.lower() for a in allergies]

        for drug_kw, condition_kw, cond_type, severity, msg in self.RULES:
            has_drug = any(drug_kw in m for m in meds_low)
            if not has_drug:
                continue

            if cond_type == "allergy":
                triggered = any(condition_kw in a for a in allergy_low)
            else:
                triggered = any(condition_kw in d for d in dis_low)

            if triggered:
                # Avoid duplicate warnings
                if not any(w["drug"].lower() == drug_kw and w["condition"].lower() == condition_kw for w in warnings):
                    warnings.append({
                        "drug": drug_kw.capitalize(),
                        "condition": condition_kw.capitalize(),
                        "condition_type": cond_type,
                        "severity": severity,
                        "warning": msg,
                        # Keep backward compat field
                        "disease_or_allergen": condition_kw.capitalize(),
                    })

        return warnings
