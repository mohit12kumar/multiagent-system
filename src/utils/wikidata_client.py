import requests
from typing import Any, Dict, Optional
from src.monitoring.logger import logger


class WikidataClient:
    def __init__(self):
        self.api_url = "https://www.wikidata.org/w/api.php"

    def search_entities(self, query: str, limit: int = 1) -> Optional[Dict[str, Any]]:
        """
        Searches Wikidata entities by query string.
        Returns the first match with details, or None.
        """
        try:
            params = {
                "action": "wbsearchentities",
                "format": "json",
                "language": "en",
                "search": query,
                "limit": limit
            }
            response = requests.get(self.api_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data and data.get("search"):
                return data["search"][0]
        except Exception as e:
            logger.warning(f"Wikidata search failed for query '{query}': {e}")
        return None

    def get_entity_details(self, wikidata_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches full details of a specific Wikidata ID.
        """
        try:
            params = {
                "action": "wbgetentities",
                "format": "json",
                "languages": "en",
                "ids": wikidata_id
            }
            response = requests.get(self.api_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data and data.get("entities") and wikidata_id in data["entities"]:
                entity = data["entities"][wikidata_id]
                description = ""
                descriptions = entity.get("descriptions", {})
                if "en" in descriptions:
                    description = descriptions["en"].get("value", "")

                label = ""
                labels = entity.get("labels", {})
                if "en" in labels:
                    label = labels["en"].get("value", "")

                return {
                    "wikidata_id": wikidata_id,
                    "label": label,
                    "description": description
                }
        except Exception as e:
            logger.warning(
                f"Wikidata detail fetch failed for ID '{wikidata_id}': {e}")
        return None
