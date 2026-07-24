import os
import csv
import requests
from typing import Optional
from src.monitoring.logger import logger


class RxNormClient:
    def __init__(self):
        self.api_url = "https://rxnav.nlm.nih.gov/REST"

        # Determine CSV gazetteer path
        BASE_DIR = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        self.gazetteer_path = os.path.join(
            BASE_DIR, "data", "gazetteers", "drug_list.csv")

    def get_rxcui(self, drug_name: str) -> Optional[str]:
        """
        Attempts to resolve drug name to RxCUI via REST API,
        falling back to local drug CSV file.
        """
        if not drug_name:
            return None

        # 1. Query live RxNorm REST API (free public API, no key required)
        try:
            url = f"{self.api_url}/rxcui.json"
            params = {"name": drug_name, "search": 2}
            response = requests.get(url, params=params, timeout=3)

            if response.status_code == 200:
                data = response.json()
                id_group = data.get("idGroup", {})
                rxnorm_ids = id_group.get("rxnormId", [])
                if rxnorm_ids:
                    logger.info(
                        f"RxNorm API resolved '{drug_name}' to RxCUI {rxnorm_ids[0]}")
                    return rxnorm_ids[0]
        except Exception as e:
            logger.warning(
                f"RxNorm API request failed for '{drug_name}' (offline/timeout): {e}")

        # 2. Fallback: Local CSV lookup
        return self._lookup_local_gazetteer(drug_name)

    def _lookup_local_gazetteer(self, drug_name: str) -> Optional[str]:
        """Searches local drug CSV file."""
        if not os.path.exists(self.gazetteer_path):
            logger.warning(
                f"Local drug gazetteer not found at {self.gazetteer_path}")
            return None

        try:
            with open(self.gazetteer_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["name"].strip().lower() == drug_name.strip().lower():
                        logger.info(
                            f"Local drug list resolved '{drug_name}' to RxCUI {row['rxnorm_id']}")
                        return row["rxnorm_id"]
        except Exception as e:
            logger.error(f"Failed to read local drug list: {e}")

        logger.info(f"RxNorm could not resolve '{drug_name}'")
        return None
