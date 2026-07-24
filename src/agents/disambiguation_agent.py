from src.models.pipeline_state import PipelineState
from src.memory.chroma_store import ChromaStore
from src.memory.mysql_store import MySQLStore
from src.medical_kb.umls_client import UmlsClient
from src.medical_kb.snomed_client import SnomedClient
from src.medical_kb.rxnorm_client import RxNormClient
from src.monitoring.logger import logger, set_log_context


class DisambiguationAgent:
    def __init__(self, config: dict, chroma_store: ChromaStore, mysql_store: MySQLStore):
        self.config = config or {}
        self.similarity_threshold = self.config.get(
            "similarity_threshold", 0.80)
        self.max_candidates = self.config.get("max_candidates", 3)
        self.chroma_store = chroma_store
        self.mysql_store = mysql_store

        # Initialize medical client registries
        self.umls_client = UmlsClient()
        self.snomed_client = SnomedClient()
        self.rxnorm_client = RxNormClient()

    def process(self, state: PipelineState) -> PipelineState:
        """
        Links clinical entity mentions to UMLS/SNOMED/RxNorm canonical profiles.
        Uses dual embedding search queries (MiniLM default -> Bio_ClinicalBERT fallback).
        """
        set_log_context(state.session_id, "disambiguation_agent")
        logger.info("Starting clinical entity linking and concept mapping")

        finalized_entities = []

        for entity in state.validated_entities:
            linked = False

            # 1. Search Chroma DB with default embedding model (MiniLM)
            candidates = self.chroma_store.query_similar_entities(
                text=entity.text,
                entity_type=entity.type,
                n_results=self.max_candidates,
                use_fallback=False
            )

            if candidates and candidates[0]["similarity"] >= self.similarity_threshold:
                best_candidate = candidates[0]
                canonical_rec = self.mysql_store.get_canonical_entity_by_id(
                    best_candidate["id"])
                if canonical_rec:
                    entity.canonical_id = canonical_rec.id
                    entity.canonical_name = canonical_rec.name
                    entity.confidence = min(0.99, entity.confidence + 0.05)
                    linked = True
                    logger.info(
                        f"Linked '{entity.text}' to local canonical profile '{canonical_rec.name}' via MiniLM search")

            # 2. Dual Embedding Fallback: Search Chroma DB using Bio_ClinicalBERT
            if not linked:
                logger.info(
                    f"Low default match similarity. Querying Chroma fallback index (Bio_ClinicalBERT) for '{entity.text}'")
                candidates = self.chroma_store.query_similar_entities(
                    text=entity.text,
                    entity_type=entity.type,
                    n_results=self.max_candidates,
                    use_fallback=True
                )
                if candidates and candidates[0]["similarity"] >= self.similarity_threshold:
                    best_candidate = candidates[0]
                    canonical_rec = self.mysql_store.get_canonical_entity_by_id(
                        best_candidate["id"])
                    if canonical_rec:
                        entity.canonical_id = canonical_rec.id
                        entity.canonical_name = canonical_rec.name
                        entity.confidence = min(0.99, entity.confidence + 0.05)
                        linked = True
                        logger.info(
                            f"Linked '{entity.text}' to local canonical profile '{canonical_rec.name}' via Bio_ClinicalBERT search")

            # 3. Medical Knowledge Base Terminology Lookup (RxNorm, SNOMED, UMLS)
            if not linked:
                logger.info(
                    f"No local vector matches above similarity limit. Querying clinical terminologies for '{entity.text}'")
                concept_id = None
                desc = f"Auto-created from terminology API. Original: {entity.text}"

                if entity.type == "DRUG":
                    concept_id = self.rxnorm_client.get_rxcui(entity.text)
                    vocab_type = "RxNorm (RxCUI)"
                elif entity.type == "DISEASE":
                    concept_id = self.snomed_client.get_snomed_code(
                        entity.text)
                    vocab_type = "SNOMED CT"
                elif entity.type == "ANATOMY":
                    concept_id = self.umls_client.get_cui(entity.text)
                    vocab_type = "UMLS CUI"

                if concept_id:
                    # Check if this name is already in MySQL to avoid conflicts
                    existing_canonical = self.mysql_store.get_canonical_entity_by_name(
                        entity.text)
                    if existing_canonical:
                        entity.canonical_id = existing_canonical.id
                        entity.canonical_name = existing_canonical.name
                        linked = True
                    else:
                        try:
                            # Create new canonical profile in MySQL
                            new_canonical = self.mysql_store.create_canonical_entity(
                                name=entity.text,
                                entity_type=entity.type,
                                description=f"{desc} (ID: {concept_id})",
                                wikidata_id=concept_id  # Store concept ID in wikidata_id column
                            )
                            # Index in Chroma DB
                            self.chroma_store.add_entity(
                                new_canonical.id, entity.text, entity.type)

                            entity.canonical_id = new_canonical.id
                            entity.canonical_name = entity.text
                            linked = True
                            logger.info(
                                f"Linked '{entity.text}' to new canonical profile via {vocab_type} ID {concept_id}")
                        except Exception as ex:
                            logger.error(
                                f"Failed to auto-create terminology profile: {ex}")

            # 4. Trigger review for low-confidence or unmatched entities
            if not linked or entity.confidence < self.similarity_threshold:
                entity.needs_review = True
                logger.info(
                    f"Flagged medical entity '{entity.text}' ({entity.type}) for human review queue")

            finalized_entities.append(entity)

        state.final_entities = finalized_entities
        state.current_stage = "FORMATTING"

        logger.info(
            f"Disambiguation complete. Linked {sum(1 for e in finalized_entities if e.canonical_id is not None)} of {len(finalized_entities)} entities.")
        return state
