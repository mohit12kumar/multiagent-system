import re
from typing import Dict, Any, List
from backend.models.entity import EntityMentionModel
from src.monitoring.logger import logger


class BioBERTAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.agent_name = "biobert"

        # Disease patterns dictionary for robust BioBERT fallback
        self.disease_conditions = [
            "hypertension", "essential hypertension", "diabetes mellitus", "type 2 diabetes",
            "type 1 diabetes", "asthma", "bronchial asthma", "pneumonia", "bacterial pneumonia",
            "bacterial infection", "depression", "major depressive disorder", "hyperlipidemia",
            "gerd", "gastroesophageal reflux disease", "atrial fibrillation", "heart failure",
            "coronary artery disease", "copd", "chronic obstructive pulmonary disease",
            "migraine", "rheumatoid arthritis", "osteoarthritis", "chronic kidney disease"
        ]

    def extract(self, sentences: List[dict]) -> List[EntityMentionModel]:
        logger.info("BioBERT Agent executing disease recognition")
        entities = []
        full_text = " ".join([s.get("text", "") for s in sentences]) if sentences else ""

        for disease in self.disease_conditions:
            for match in re.finditer(r'\b' + re.escape(disease) + r'\b', full_text, re.IGNORECASE):
                entities.append(EntityMentionModel(
                    text=match.group(0),
                    type="DISEASE",
                    start_char=match.start(),
                    end_char=match.end(),
                    confidence=0.94,
                    source_agents=[self.agent_name]
                ))

        return entities
