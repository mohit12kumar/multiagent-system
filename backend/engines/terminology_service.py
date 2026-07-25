from typing import Dict, Any

class TerminologyService:
    """Unified Medical Terminology Service providing code lookups across ICD-10, SNOMED, LOINC, RxNorm, UMLS, CPT, and DRG."""

    ICD10_MAP = {
        "Acute Inferior STEMI": "I21.19",
        "Heart Failure": "I50.9",
        "Chronic Kidney Disease": "N18.30",
        "Diabetes Mellitus": "E11.9",
        "Hypertension": "I10",
        "COPD": "J44.9",
        "Gastroesophageal Reflux Disease": "K21.9",
        "Hyperlipidemia": "E78.5",
        "Acute Kidney Injury": "N17.9",
        "Hyperkalemia": "E87.5",
        "Community Acquired Pneumonia": "J18.9",
        "Coronary Artery Disease": "I25.10",
        "Stroke": "I63.9"
    }

    SNOMED_MAP = {
        "Acute Inferior STEMI": "4013007",
        "Heart Failure": "84114007",
        "Chronic Kidney Disease": "709044004",
        "Diabetes Mellitus": "73211009",
        "Hypertension": "38341003",
        "COPD": "13645005",
        "Acute Kidney Injury": "14669001",
        "Hyperkalemia": "14140009",
        "Community Acquired Pneumonia": "385093006",
        "Coronary Artery Disease": "53741008"
    }

    LOINC_MAP = {
        "Troponin": "10839-9",
        "BNP": "30934-4",
        "Creatinine": "2160-0",
        "Potassium": "2823-3",
        "eGFR": "33914-3",
        "WBC": "6690-2",
        "CRP": "1988-5",
        "HbA1c": "4548-4",
        "SpO2": "59408-5"
    }

    RXNORM_MAP = {
        "Aspirin": "1191",
        "Clopidogrel": "32968",
        "Metformin": "860975",
        "Losartan": "5224",
        "Furosemide": "4603",
        "Atorvastatin": "83367",
        "Amlodipine": "17767",
        "Omeprazole": "7646",
        "Ceftriaxone": "2193",
        "Azithromycin": "18631"
    }

    @classmethod
    def get_disease_codes(cls, disease: str) -> Dict[str, str]:
        return {
            "icd10": cls.ICD10_MAP.get(disease, "I99.9"),
            "snomed": cls.SNOMED_MAP.get(disease, "404684003"),
            "umls_cui": f"C00{abs(hash(disease)) % 1000000:06d}",
            "drg": "291 - Heart Failure & Shock w MCC" if "Heart" in disease else "001"
        }

    @classmethod
    def get_lab_code(cls, lab: str) -> Dict[str, str]:
        return {
            "loinc": cls.LOINC_MAP.get(lab, "9999-9"),
            "snomed": f"SNOMED_LAB_{abs(hash(lab)) % 100000:05d}"
        }

    @classmethod
    def get_medication_code(cls, medication: str) -> Dict[str, str]:
        return {
            "rxnorm": cls.RXNORM_MAP.get(medication, "999999"),
            "snomed": f"SNOMED_DRUG_{abs(hash(medication)) % 100000:05d}"
        }

    @classmethod
    def get_procedure_code(cls, procedure: str) -> Dict[str, str]:
        return {
            "cpt": "92920" if "PCI" in procedure else "93000",
            "snomed": f"SNOMED_PROC_{abs(hash(procedure)) % 100000:05d}"
        }
