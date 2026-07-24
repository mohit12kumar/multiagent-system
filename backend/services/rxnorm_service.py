import requests
from typing import Dict, Any, Optional
from src.monitoring.logger import logger


class RxNormService:
    BASE_URL = "https://rxnav.nlm.nih.gov/REST"

    @classmethod
    def get_rxcui(cls, drug_name: str) -> Optional[str]:
        """Queries free NIH RxNorm API for RXCUI code for a drug name."""
        try:
            url = f"{cls.BASE_URL}/rxcui.json"
            params = {"name": drug_name}
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                id_group = data.get("idGroup", {})
                rx_concept_properties = id_group.get("rxnormId", [])
                if rx_concept_properties:
                    return rx_concept_properties[0]
            return None
        except Exception as e:
            logger.warning(f"RxNorm lookup failed for '{drug_name}': {e}")
            return None

    @classmethod
    def validate_drug(cls, drug_name: str) -> Dict[str, Any]:
        """Validates drug name existence via RxNorm API."""
        rxcui = cls.get_rxcui(drug_name)
        if rxcui:
            return {"valid": True, "rxcui": rxcui, "source": "RxNorm"}
        return {"valid": False, "rxcui": None, "source": "RxNorm"}
