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
        # Metformin in renal failure / eGFR < 30 / AKI
        ("metformin",     "ckd",          "disease",  "Critical", "Metformin strictly contraindicated in eGFR < 30 (CKD Stage IV/V) due to high risk of fatal lactic acidosis. Hold immediately."),
        ("metphormin",    "ckd",          "disease",  "Critical", "Metformin strictly contraindicated in eGFR < 30 (CKD Stage IV/V) due to high risk of fatal lactic acidosis. Hold immediately."),
        ("metformin",     "kidney",       "disease",  "Critical", "Metformin carries severe lactic acidosis risk in renal insufficiency (eGFR < 30 / AKI). Hold immediately."),
        ("metformin",     "aki",          "disease",  "Critical", "Metformin strictly contraindicated in Acute Kidney Injury due to risk of lactic acidosis. Hold therapy."),
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
        ("lisinopril",    "hyperkalemia", "disease",  "Major",    "ACE inhibitors (Lisinopril) are relatively contraindicated with severe hyperkalemia (K+ > 5.5 mmol/L). Hold and recheck potassium."),
        ("losartan",      "hyperkalemia", "disease",  "Major",    "ARBs (Losartan) are relatively contraindicated with hyperkalemia (Potassium > 5.0 mmol/L). Monitor potassium STAT."),
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
        """Check for contraindications across drug-disease pairs, allergy conflicts, DAPT monitoring, and duplicate statins."""
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
                    d_name = drug_kw.capitalize()
                    c_name = condition_kw.capitalize()
                    risk = "Lactic Acidosis" if "metformin" in drug_kw else ("Hyperkalemia" if "hyperkalemia" in condition_kw or "spironolactone" in drug_kw else ("Nephrotoxicity" if "ckd" in condition_kw or "kidney" in condition_kw else "Adverse Event"))
                    rec = f"Hold {d_name}" if "metformin" in drug_kw else (f"Monitor ECG STAT" if "losartan" in drug_kw else (f"Discontinue {d_name}" if "ibuprofen" in drug_kw or "naproxen" in drug_kw else f"Review {d_name} regimen"))

                    warnings.append({
                        "drug": d_name,
                        "condition": c_name,
                        "condition_type": cond_type,
                        "severity": severity,
                        "reason": f"{c_name} documented with {d_name}",
                        "risk": risk,
                        "recommendation": rec,
                        "warning": msg,
                        # Keep backward compat field
                        "disease_or_allergen": c_name,
                    })

        # Dual Antiplatelet Therapy (DAPT) Monitoring check
        has_aspirin = any("aspirin" in m for m in meds_low)
        has_clopidogrel = any("clopidogrel" in m or "plavix" in m for m in meds_low)
        if has_aspirin and has_clopidogrel:
            warnings.append({
                "drug": "Aspirin + Clopidogrel",
                "condition": "STEMI / CAD",
                "condition_type": "combination",
                "severity": "Moderate (Monitoring Required)",
                "reason": "Dual Antiplatelet Therapy (DAPT) active",
                "risk": "Gastrointestinal & Systemic Bleeding",
                "recommendation": "Monitor for Bleeding & Coagulation Status",
                "warning": "Dual Antiplatelet Therapy (DAPT) active: Essential for post-PCI/STEMI, but requires close monitoring for gastrointestinal and systemic bleeding.",
                "disease_or_allergen": "STEMI / CAD"
            })

        # Duplicate Statin Therapy check
        statins = [m for m in meds_low if any(s in m for s in ["atorvastatin", "rosuvastatin", "simvastatin", "pravastatin"])]
        if len(set(statins)) > 1:
            warnings.append({
                "drug": "Duplicate Statins",
                "condition": "Hyperlipidemia",
                "condition_type": "duplicate",
                "severity": "Major",
                "reason": f"Multiple statins prescribed ({', '.join(statins)})",
                "risk": "Rhabdomyolysis & Hepatotoxicity",
                "recommendation": "Discontinue Redundant Statin",
                "warning": f"Duplicate statin therapy detected ({', '.join(statins)}). Risk of rhabdomyolysis and hepatotoxicity. Discontinue redundant statin.",
                "disease_or_allergen": "Hyperlipidemia"
            })

        return warnings
