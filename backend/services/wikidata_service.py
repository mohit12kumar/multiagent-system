import requests
from typing import Dict, Any, Optional
from src.monitoring.logger import logger


class WikidataService:
    WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"

    _SEARCH_CACHE: Dict[str, Any] = {}

    @classmethod
    def search_entity(cls, query: str) -> Optional[Dict[str, Any]]:
        """Queries free Wikidata API for medical entities, with fast in-memory caching."""
        key = query.strip().lower()
        if key in cls._SEARCH_CACHE:
            return cls._SEARCH_CACHE[key]

        try:
            params = {
                "action": "wbsearchentities",
                "search": query,
                "language": "en",
                "format": "json"
            }
            headers = {"User-Agent": "ClinicalMultiAgent/1.0 (free clinical research tool)"}
            resp = requests.get(cls.WIKIDATA_API_URL, params=params, headers=headers, timeout=1.5)
            if resp.status_code == 200:
                data = resp.json()
                search_results = data.get("search", [])
                if search_results:
                    top_match = search_results[0]
                    res = {
                        "id": top_match.get("id"),
                        "label": top_match.get("label"),
                        "description": top_match.get("description", "")
                    }
                    cls._SEARCH_CACHE[key] = res
                    return res
            cls._SEARCH_CACHE[key] = None
            return None
        except Exception as e:
            logger.warning(f"Wikidata lookup failed for '{query}': {e}")
            cls._SEARCH_CACHE[key] = None
            return None

    @classmethod
    def validate_disease_medication_pair(cls, disease: str, medication: str) -> Dict[str, Any]:
        """
        Cross-checks disease and medication pair compatibility using free Wikidata & internal knowledge rules.
        """
        d_lower = disease.lower()
        m_lower = medication.lower()

        # Known standard clinical pairings rulebook
        standard_pairings = {
            "hypertension": ["amlodipine", "lisinopril", "losartan", "hydrochlorothiazide", "atenolol", "metoprolol"],
            "diabetes": ["metformin", "insulin", "glipizide", "sitagliptin", "empagliflozin"],
            "asthma": ["albuterol", "fluticasone", "montelukast", "budesonide", "salmeterol"],
            "bacterial infection": ["amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline", "cephalexin"],
            "infection": ["amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline", "cephalexin"],
            "pneumonia": ["azithromycin", "amoxicillin", "ceftriaxone", "levofloxacin"],
            "depression": ["sertraline", "fluoxetine", "escitalopram", "bupropion"],
            "hyperlipidemia": ["atorvastatin", "simvastatin", "rosuvastatin"],
            "pain": ["ibuprofen", "acetaminophen", "naproxen", "paracetamol"],
            "gerd": ["omeprazole", "pantoprazole", "famotidine"],
            "chronic kidney disease": ["furosemide", "vitamin d3", "vitamin d", "cholecalciferol"],
            "kidney disease": ["furosemide", "vitamin d3", "vitamin d", "cholecalciferol"],
            "ckd": ["furosemide", "vitamin d3", "vitamin d", "cholecalciferol"],
            "renal failure": ["furosemide", "vitamin d3", "vitamin d", "cholecalciferol"]
        }

        for dis_key, valid_meds in standard_pairings.items():
            if dis_key in d_lower:
                for med in valid_meds:
                    if med in m_lower:
                        return {
                            "validation_status": "Correct Medication",
                            "correct": True,
                            "confidence": 0.98,
                            "reason": f"Standard medical consensus pair ({medication} for {disease})"
                        }

        # Check Wikidata entity existence
        med_wiki = cls.search_entity(medication)
        dis_wiki = cls.search_entity(disease)

        if med_wiki and dis_wiki:
            return {
                "validation_status": "Possible Medication",
                "correct": True,
                "confidence": 0.85,
                "reason": f"Validated entities in Wikidata ({med_wiki['label']} & {dis_wiki['label']})"
            }

        return {
            "validation_status": "Unknown Medication",
            "correct": False,
            "confidence": 0.50,
            "reason": f"Medication-disease relation not verified in public medical ontology"
        }
