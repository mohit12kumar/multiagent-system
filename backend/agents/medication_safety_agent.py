"""
Medication Safety Agent.
Performs duplicate therapy detection, dosage safety range checks, and drug class / indication mapping.
"""

from typing import Dict, Any, List, Tuple
from src.monitoring.logger import logger

_DRUG_CLASS_MAP = {
    "amlodipine": ("Calcium Channel Blocker (CCB)", "Hypertension"),
    "nifedipine": ("Calcium Channel Blocker (CCB)", "Hypertension"),
    "diltiazem": ("Calcium Channel Blocker (CCB)", "Hypertension"),
    "verapamil": ("Calcium Channel Blocker (CCB)", "Hypertension"),
    "omeprazole": ("Proton Pump Inhibitor (PPI)", "GERD / Acid Reflux"),
    "pantoprazole": ("Proton Pump Inhibitor (PPI)", "GERD / Acid Reflux"),
    "rabeprazole": ("Proton Pump Inhibitor (PPI)", "GERD / Acid Reflux"),
    "azithromycin": ("Macrolide Antibiotic", "Bacterial Infection / Pneumonia"),
    "clarithromycin": ("Macrolide Antibiotic", "Bacterial Infection"),
    "erythromycin": ("Macrolide Antibiotic", "Bacterial Infection"),
    "metformin": ("Biguanide Antidiabetic Agent", "Type 2 Diabetes Mellitus"),
    "salbutamol": ("Short-Acting Beta-Agonist (SABA)", "COPD / Asthma Bronchospasm"),
    "albuterol": ("Short-Acting Beta-Agonist (SABA)", "COPD / Asthma Bronchospasm"),
    "atorvastatin": ("HMG-CoA Reductase Inhibitor (Statin)", "Hyperlipidemia / CV Risk"),
    "rosuvastatin": ("HMG-CoA Reductase Inhibitor (Statin)", "Hyperlipidemia / CV Risk"),
    "simvastatin": ("HMG-CoA Reductase Inhibitor (Statin)", "Hyperlipidemia"),
    "furosemide": ("Loop Diuretic", "Fluid Overload / CHF / CKD Edema"),
    "torsemide": ("Loop Diuretic", "Fluid Overload / CHF Edema"),
    "losartan": ("Angiotensin II Receptor Blocker (ARB)", "Hypertension / CKD"),
    "valsartan": ("Angiotensin II Receptor Blocker (ARB)", "Hypertension"),
    "telmisartan": ("Angiotensin II Receptor Blocker (ARB)", "Hypertension"),
    "lisinopril": ("ACE Inhibitor", "Hypertension / Heart Failure"),
    "enalapril": ("ACE Inhibitor", "Hypertension"),
    "ramipril": ("ACE Inhibitor", "Hypertension"),
    "paracetamol": ("Analgesic & Antipyretic", "Fever & Pain Management"),
    "acetaminophen": ("Analgesic & Antipyretic", "Fever & Pain Management"),
    "aspirin": ("Antiplatelet / NSAID", "Cardiovascular Prophylaxis"),
    "clopidogrel": ("P2Y12 Antiplatelet Agent", "Cardiovascular Prophylaxis"),
}

# Max safe daily doses in mg (or units)
_MAX_DAILY_DOSES = {
    "metformin": 2000,
    "paracetamol": 4000,
    "acetaminophen": 4000,
    "amlodipine": 10,
    "atorvastatin": 80,
    "omeprazole": 40,
    "furosemide": 240,
    "losartan": 100,
    "azithromycin": 500,
}


class MedicationSafetyAgent:
    """Performs duplicate therapy detection, dosage safety validation, and drug class mapping."""

    @classmethod
    def get_drug_class_and_indication(cls, drug_name: str) -> Tuple[str, str]:
        """Returns (Drug Class, Primary Indication)."""
        d_low = drug_name.lower().strip()
        for k, (d_class, ind) in _DRUG_CLASS_MAP.items():
            if k in d_low:
                return d_class, ind
        return "Pharmaceutical Agent", "Clinical Indication"

    @classmethod
    def audit_medications(cls, medications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Audits medications for duplicate therapy and dosage range safety.
        Returns: { 'duplicate_alerts': List[str], 'dosage_warnings': List[str], 'enriched_medications': List[Dict] }
        """
        duplicate_alerts = []
        dosage_warnings = []
        seen_drugs: Dict[str, List[Dict[str, Any]]] = {}

        for m in medications:
            name = m.get("name", "").strip()
            if not name:
                continue
            base_name = name.lower().split()[0]
            if base_name not in seen_drugs:
                seen_drugs[base_name] = []
            seen_drugs[base_name].append(m)

        # 1. Duplicate Therapy Check
        for base_name, med_list in seen_drugs.items():
            if len(med_list) > 1:
                names_str = ", ".join([f"{m.get('name')} ({m.get('dosage')})" for m in med_list])
                duplicate_alerts.append(
                    f"Duplicate Therapy Detected: Multiple formulations/doses of {base_name.title()} prescribed ({names_str}). Doctor Review Required."
                )

        # 2. Dosage Safety Range Check
        enriched_meds = []
        for m in medications:
            m_copy = dict(m)
            name = m_copy.get("name", "").lower()
            d_class, ind = cls.get_drug_class_and_indication(name)
            m_copy["drug_class"] = d_class
            m_copy["indication"] = ind

            # Parse dosage for max dose check
            dosage_str = m_copy.get("dosage", "")
            freq_str = m_copy.get("frequency", "")
            
            # Simple numeric multiplier
            multiplier = 1
            if "three" in freq_str.lower() or "tds" in freq_str.lower() or "tid" in freq_str.lower():
                multiplier = 3
            elif "twice" in freq_str.lower() or "bd" in freq_str.lower() or "bid" in freq_str.lower():
                multiplier = 2
            elif "four" in freq_str.lower() or "qid" in freq_str.lower():
                multiplier = 4

            for k, max_d in _MAX_DAILY_DOSES.items():
                if k in name and "mg" in dosage_str.lower():
                    try:
                        digits = int(''.join(filter(str.isdigit, dosage_str)))
                        total_daily = digits * multiplier
                        if total_daily > max_d:
                            msg = f"{m_copy.get('name')} dosage ({dosage_str} {freq_str} = {total_daily} mg/day) exceeds recommended maximum daily limit of {max_d} mg/day."
                            dosage_warnings.append(msg)
                            m_copy["clinical_warning"] = msg
                            m_copy["validation_status"] = "Dosage Safety Warning"
                    except Exception:
                        pass
            enriched_meds.append(m_copy)

        if duplicate_alerts or dosage_warnings:
            logger.warning(f"Medication Safety Audit: {len(duplicate_alerts)} duplicate alert(s), {len(dosage_warnings)} dosage warning(s).")

        return {
            "duplicate_alerts": duplicate_alerts,
            "dosage_warnings": dosage_warnings,
            "enriched_medications": enriched_meds
        }
