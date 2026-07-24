import os
import csv
from typing import Optional
from src.monitoring.logger import logger


class UmlsClient:
    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        self.gazetteer_path = os.path.join(
            BASE_DIR, "data", "gazetteers", "anatomy_terms.csv")

    def get_cui(self, concept_name: str) -> Optional[str]:
        """
        Resolves general concepts/anatomy to UMLS CUIs.
        Reads from local anatomy terms list.
        """
        if not concept_name:
            return None

        if not os.path.exists(self.gazetteer_path):
            logger.warning(
                f"Local anatomy list not found at {self.gazetteer_path}")
            return None

        try:
            with open(self.gazetteer_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["name"].strip().lower() == concept_name.strip().lower():
                        logger.info(
                            f"Local anatomy list resolved '{concept_name}' to CUI {row['cui']}")
                        return row["cui"]
        except Exception as e:
            logger.error(f"Failed to read local anatomy list: {e}")

        logger.info(f"UMLS could not resolve '{concept_name}'")
        return None
