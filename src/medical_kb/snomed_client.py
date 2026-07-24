import os
import csv
from typing import Optional
from src.monitoring.logger import logger


class SnomedClient:
    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        self.gazetteer_path = os.path.join(
            BASE_DIR, "data", "gazetteers", "disease_list.csv")

    def get_snomed_code(self, disease_name: str) -> Optional[str]:
        """
        Resolves clinical condition to SNOMED CT code.
        Reads from local disease gazetteer.
        """
        if not disease_name:
            return None

        if not os.path.exists(self.gazetteer_path):
            logger.warning(
                f"Local disease list not found at {self.gazetteer_path}")
            return None

        try:
            with open(self.gazetteer_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Check exact or case insensitive match
                    if row["name"].strip().lower() == disease_name.strip().lower():
                        logger.info(
                            f"Local disease list resolved '{disease_name}' to SNOMED {row['snomed_code']}")
                        return row["snomed_code"]
        except Exception as e:
            logger.error(f"Failed to read local disease list: {e}")

        logger.info(f"SNOMED could not resolve '{disease_name}'")
        return None
