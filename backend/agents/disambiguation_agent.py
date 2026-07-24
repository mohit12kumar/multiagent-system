from typing import Dict, Any, Optional
from backend.models.pipeline_state import PipelineState
from backend.services.chroma_service import ChromaService
from backend.database.mysql_store import MySQLStore
from src.monitoring.logger import logger


class DisambiguationAgent:
    def __init__(self, config: Dict[str, Any] = None, chroma_service: ChromaService = None, mysql_store: Optional[MySQLStore] = None):
        self.config = config or {}
        self.chroma = chroma_service or ChromaService()
        self.mysql_store = mysql_store

    def process(self, state: PipelineState) -> PipelineState:
        logger.info(f"Disambiguation Agent running vector similarity normalization for session {state.session_id}")

        seen_canonicals = set()
        for ent in state.validated_entities:
            matches = self.chroma.query_similar_entities(ent.text, entity_type=ent.type, n_results=1)
            if matches and matches[0].get("similarity", 0) > 0.85:
                top_match = matches[0]
                canon_name = top_match.get("name")
            else:
                canon_name = ent.text.strip().title()

            if self.mysql_store:
                try:
                    canon_obj = self.mysql_store.get_or_create_canonical_entity(canon_name, ent.type)
                    ent.canonical_id = canon_obj.id
                    ent.canonical_name = canon_obj.name
                    if canon_obj.name not in seen_canonicals:
                        seen_canonicals.add(canon_obj.name)
                        self.chroma.add_entity(canon_obj.id, canon_obj.name, ent.type)
                except Exception as e:
                    logger.warning(f"Canonical entity DB creation error: {e}")
                    ent.canonical_id = None
                    ent.canonical_name = canon_name
            else:
                c_id = f"canon_{ent.text.lower().replace(' ', '_')}"
                ent.canonical_id = None
                ent.canonical_name = canon_name

        state.final_entities = state.validated_entities
        logger.info("Disambiguation Agent complete.")
        return state
