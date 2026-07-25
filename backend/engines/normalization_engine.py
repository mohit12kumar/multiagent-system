class NormalizationEngine:
    """Normalizes medical terminology across diseases, symptoms, labs, vitals, and medications."""

    DISEASE_SYNONYM_MAP = {
        "htn": "Hypertension",
        "high bp": "Hypertension",
        "essential hypertension": "Hypertension",
        "cap": "Community Acquired Pneumonia",
        "pneumonia": "Community Acquired Pneumonia",
        "dm": "Diabetes Mellitus",
        "type 2 diabetes": "Diabetes Mellitus",
        "ckd": "Chronic Kidney Disease",
        "mi": "Acute Inferior STEMI",
        "stemi": "Acute Inferior STEMI",
        "copd": "COPD",
        "cad": "Coronary Artery Disease",
        "aki": "Acute Kidney Injury",
        "gerd": "Gastroesophageal Reflux Disease",
        "tb": "Tuberculosis"
    }

    LAB_SYNONYM_MAP = {
        "k": "Potassium",
        "potassium": "Potassium",
        "cr": "Creatinine",
        "creatinine": "Creatinine",
        "egfr": "eGFR",
        "bnp": "BNP",
        "trop": "Troponin",
        "troponin": "Troponin",
        "wbc": "WBC",
        "crp": "CRP"
    }

    @classmethod
    def normalize_disease(cls, term: str) -> str:
        t_low = term.strip().lower()
        return cls.DISEASE_SYNONYM_MAP.get(t_low, term.strip().title())

    @classmethod
    def normalize_lab(cls, term: str) -> str:
        t_low = term.strip().lower()
        return cls.LAB_SYNONYM_MAP.get(t_low, term.strip().title())

    @classmethod
    def normalize_medication(cls, term: str) -> str:
        return term.strip().capitalize()
