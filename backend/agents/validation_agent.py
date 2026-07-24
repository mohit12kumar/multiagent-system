from typing import Dict, Any, List
from backend.models.pipeline_state import PipelineState
from backend.models.entity import EntityMentionModel
from src.monitoring.logger import logger


class ValidationAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.valid_types = {
            "DISEASE", "DRUG", "SYMPTOM", "ANATOMY", "PROCEDURE",
            "DOSAGE", "FREQUENCY", "DURATION", "ROUTE", "DATE", "TIME", "LAB_VALUE", "ALLERGY"
        }
        self.min_confidence_threshold = self.config.get("min_confidence_threshold", 0.60)
        self.review_threshold = self.config.get("review_threshold", 0.75)

        # Stop words / invalid entity texts to purge
        self.blacklisted_terms = {"patient", "doctor", "hospital", "clinic", "treatment", "day", "days", "note", "report", "the", "and"}

    def process(self, state: PipelineState) -> PipelineState:
        logger.info(f"Executing Validation Agent for session {state.session_id}")
        input_entities = state.aggregated_entities
        validated: List[EntityMentionModel] = []
        sections = state.metadata.get("sections", [])

        def get_section_for_char(pos: int) -> str:
            for s in sections:
                if s["start"] <= pos < s["end"]:
                    return s["name"]
            return "UNKNOWN"

        for ent in input_entities:
            clean_text = ent.text.strip().lower()

            # Context-Aware Entity Classification
            sec = get_section_for_char(ent.start_char)

            # Penicillin mapping
            if "penicillin" in clean_text:
                if sec == "ALLERGIES":
                    ent.type = "ALLERGY"
                else:
                    ent.type = "DRUG"

            # Allergy keywords mapping
            if "allergy" in clean_text or "allergic" in clean_text:
                ent.type = "ALLERGY"

            # Block lab markers from becoming medications
            lab_keywords = {"creatinine", "ldl", "hemoglobin", "egfr", "potassium", "sodium", "hba1c", "wbc", "crp", "bun"}
            if clean_text in lab_keywords:
                ent.type = "LAB_VALUE"

            # 1. Taxonomy type check
            if ent.type not in self.valid_types:
                logger.debug(f"Rejecting entity '{ent.text}': invalid taxonomy type {ent.type}")
                continue

            # 2. Blacklisted non-medical term check
            if clean_text in self.blacklisted_terms or len(clean_text) < 2:
                logger.debug(f"Rejecting entity '{ent.text}': blacklisted or trivial term")
                continue

            # 3. Minimum confidence check
            if ent.confidence < self.min_confidence_threshold:
                logger.debug(f"Rejecting entity '{ent.text}': confidence {ent.confidence} below minimum threshold {self.min_confidence_threshold}")
                continue

            # 4. Review flag assignment
            if ent.confidence < self.review_threshold:
                ent.needs_review = True

            validated.append(ent)

        state.validated_entities = validated
        logger.info(f"Validation Agent complete. Validated {len(validated)} entities.")
        return state
