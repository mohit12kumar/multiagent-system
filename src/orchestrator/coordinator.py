import os
import uuid
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

# Import models & store
from src.models.pipeline_state import PipelineState
from src.models.entity import EntityMentionModel
from src.memory.mysql_store import MySQLStore
from src.memory.chroma_store import ChromaStore
from src.db.models import Document

# Import agents
from src.agents.preprocessing_agent import PreprocessingAgent
from src.agents.phi_redaction_agent import PHIRedactionAgent
from src.agents.extraction.scispacy_agent import ScispacyAgent
from src.agents.extraction.biobert_agent import BiobertAgent
from src.agents.extraction.groq_agent import GroqAgent
from src.agents.extraction.dosage_frequency_agent import DosageFrequencyAgent
from src.agents.aggregation_agent import AggregationAgent
from src.agents.validation_agent import ValidationAgent
from src.agents.disambiguation_agent import DisambiguationAgent
from src.agents.formatting_agent import FormattingAgent

# Import router
from src.orchestrator.router import Router
from src.monitoring.logger import logger, set_log_context

# Try importing LangSmith tracing
try:
    from langsmith.run_helpers import traceable
except ImportError:
    # Safe mock decorator if langsmith is not yet installed or import fails
    def traceable(run_type: str = "chain", name: Optional[str] = None):
        def decorator(func):
            return func
        return decorator


class Coordinator:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.mysql_store = MySQLStore(db_session)
        self.chroma_store = ChromaStore()

        # Load configuration files
        BASE_DIR = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        AGENTS_CONFIG = os.path.join(BASE_DIR, "config", "agents.yaml")
        PIPELINE_CONFIG = os.path.join(BASE_DIR, "config", "pipeline.yaml")

        self.agents_cfg = {}
        self.pipeline_cfg = {}

        if os.path.exists(AGENTS_CONFIG):
            with open(AGENTS_CONFIG, "r") as f:
                self.agents_cfg = yaml.safe_load(f) or {}

        if os.path.exists(PIPELINE_CONFIG):
            with open(PIPELINE_CONFIG, "r") as f:
                config_data = yaml.safe_load(f) or {}
                self.pipeline_cfg = config_data.get("pipeline", {})
                self.fallback_routes = config_data.get("fallback_routes", {})
                self.review_cfg = config_data.get("review_queue", {})

        # Initialize pipeline agents
        self.preprocessing_agent = PreprocessingAgent(
            self.agents_cfg.get("preprocessing_agent", {}))
        self.phi_redaction_agent = PHIRedactionAgent(
            self.agents_cfg.get("phi_redaction_agent", {}), self.mysql_store)
        self.scispacy_agent = ScispacyAgent(
            self.agents_cfg.get("scispacy_agent", {}))
        self.biobert_agent = BiobertAgent(
            self.agents_cfg.get("biobert_agent", {}))
        self.groq_agent = GroqAgent(self.agents_cfg.get("groq_agent", {}))
        self.dosage_frequency_agent = DosageFrequencyAgent(
            self.agents_cfg.get("dosage_frequency_agent", {}))
        self.aggregation_agent = AggregationAgent(
            self.agents_cfg.get("aggregation_agent", {}))
        self.validation_agent = ValidationAgent(
            self.agents_cfg.get("validation_agent", {}))
        self.disambiguation_agent = DisambiguationAgent(
            self.agents_cfg.get("disambiguation_agent", {}),
            self.chroma_store,
            self.mysql_store
        )
        self.formatting_agent = FormattingAgent(
            self.agents_cfg.get("formatting_agent", {}))
        self.router = Router()

    @traceable(run_type="chain", name="NER Orchestrator Pipeline")
    def run_pipeline(self, document_content: str, doc_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Coordinates document named entity recognition processing end-to-end.
        """
        # 1. Initialize identifiers
        doc_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        set_log_context(session_id, "coordinator")
        logger.info(
            f"Initiating pipeline session {session_id} for new document")

        # 2. Persist Document and Session in MySQL database
        self.mysql_store.create_document(
            doc_id, document_content, doc_metadata)
        self.mysql_store.create_session(session_id, doc_id)

        # Create state tracking Pydantic model
        state = PipelineState(
            session_id=session_id,
            document_id=doc_id,
            text=document_content,
            status="IN_PROGRESS",
            current_stage="PREPROCESSING",
            metadata=doc_metadata or {}
        )

        try:
            # 3. Preprocessing
            self.mysql_store.update_session(
                session_id, "IN_PROGRESS", "PREPROCESSING")
            state = self.preprocessing_agent.process(state)
            if state.status == "FAILED":
                raise Exception(state.error_message)

            # 3.5. HIPAA PHI Redaction
            self.mysql_store.update_session(
                session_id, "IN_PROGRESS", "PHI_REDACTION")
            state = self.phi_redaction_agent.process(state)
            if state.status == "FAILED":
                raise Exception(state.error_message)

            # Update Document content in DB to be redacted
            doc = self.db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.content = state.text
                self.db.commit()

            # 4. Route text to selected extraction agents
            self.mysql_store.update_session(
                session_id, "IN_PROGRESS", "EXTRACTION")
            active_extractors = self.router.route(state)

            # Execute extractions
            raw_extractions = self._execute_extraction_agents(
                active_extractors, state.sentences)
            state.raw_extractions = raw_extractions

            # 5. Aggregation & Consensus
            self.mysql_store.update_session(
                session_id, "IN_PROGRESS", "AGGREGATION")
            state = self.aggregation_agent.process(state)
            if state.status == "FAILED":
                raise Exception(state.error_message)

            # 6. Validation against taxonomy
            self.mysql_store.update_session(
                session_id, "IN_PROGRESS", "VALIDATION")
            state = self.validation_agent.process(state)
            if state.status == "FAILED":
                raise Exception(state.error_message)

            # 7. Disambiguation / Entity Linking
            self.mysql_store.update_session(
                session_id, "IN_PROGRESS", "DISAMBIGUATION")
            state = self.disambiguation_agent.process(state)
            if state.status == "FAILED":
                raise Exception(state.error_message)

            # 8. Formatting output
            self.mysql_store.update_session(
                session_id, "IN_PROGRESS", "FORMATTING")
            formatted_output = self.formatting_agent.process(state)

            # 9. Save final mentions to MySQL (and review items)
            # Check review queue threshold settings
            role = doc_metadata.get(
                "role", "doctor") if doc_metadata else "doctor"
            for ent in state.final_entities:
                # If confidence is lower than review threshold, mark needs review
                low_conf_threshold = self.review_cfg.get(
                    "low_confidence_threshold", 0.70)
                if role == "user":
                    ent.needs_review = True
                elif self.review_cfg.get("auto_queue_low_confidence", True) and ent.confidence < low_conf_threshold:
                    ent.needs_review = True

            raw_mentions = []
            for ent in state.final_entities:
                raw_mentions.append({
                    "text": ent.text,
                    "type": ent.type,
                    "start_char": ent.start_char,
                    "end_char": ent.end_char,
                    "confidence": ent.confidence,
                    "source_agents": ent.source_agents,
                    "canonical_id": ent.canonical_id,
                    "needs_review": ent.needs_review
                })

            self.mysql_store.save_entity_mentions(
                session_id, doc_id, raw_mentions)

            # Update session database status to completed
            self.mysql_store.update_session(
                session_id, "COMPLETED", "FORMATTING")

            return formatted_output

        except Exception as e:
            logger.error(
                f"Pipeline execution failed for session {session_id}: {e}", exc_info=True)
            self.mysql_store.update_session(
                session_id, "FAILED", state.current_stage, str(e))
            return {
                "session_id": session_id,
                "document_id": doc_id,
                "status": "FAILED",
                "current_stage": state.current_stage,
                "error_message": str(e)
            }

    def _execute_extraction_agents(self, active_extractors: List[str], sentences: List[dict]) -> Dict[str, List[EntityMentionModel]]:
        """Executes active extraction agents, managing parallel tasks and fallback configurations."""
        raw_extractions = {}

        # Parallel extraction execution if configured
        use_parallel = self.pipeline_cfg.get("parallel_extraction", True)

        if use_parallel and len(active_extractors) > 1:
            logger.info("Executing extraction agents in parallel")
            with ThreadPoolExecutor(max_workers=len(active_extractors)) as executor:
                # Map futures to agent names
                future_to_agent = {
                    executor.submit(self._run_single_extractor_trace, agent_name, sentences): agent_name
                    for agent_name in active_extractors
                }

                for future in as_completed(future_to_agent):
                    agent_name = future_to_agent[future]
                    try:
                        results = future.result()
                        raw_extractions[agent_name] = results
                    except Exception as e:
                        logger.error(
                            f"Parallel agent '{agent_name}' failed: {e}")
                        # Execute fallback behavior
                        raw_extractions[agent_name] = self._handle_extractor_failure(
                            agent_name, sentences)
        else:
            logger.info("Executing extraction agents sequentially")
            for agent_name in active_extractors:
                try:
                    results = self._run_single_extractor_trace(
                        agent_name, sentences)
                    raw_extractions[agent_name] = results
                except Exception as e:
                    logger.error(
                        f"Sequential agent '{agent_name}' failed: {e}")
                    # Execute fallback behavior
                    raw_extractions[agent_name] = self._handle_extractor_failure(
                        agent_name, sentences)

        return raw_extractions

    def _run_single_extractor(self, agent_name: str, sentences: List[dict]) -> List[EntityMentionModel]:
        """Runs the specific extraction logic for a single agent name."""
        if agent_name == "scispacy":
            return self.scispacy_agent.extract(sentences)
        elif agent_name == "biobert":
            return self.biobert_agent.extract(sentences)
        elif agent_name == "groq":
            return self.groq_agent.extract(sentences)
        elif agent_name == "dosage_frequency":
            return self.dosage_frequency_agent.extract(sentences)
        else:
            logger.warning(f"Unknown extraction agent: {agent_name}")
            return []

    def _run_single_extractor_trace(self, agent_name: str, sentences: List[dict]) -> List[EntityMentionModel]:
        """Wraps extractor run inside a LangSmith traceable span."""
        # Map run types for langsmith
        run_type = "llm" if agent_name in ("biobert", "groq") else "parser"

        # Wrapped call for LangSmith client
        @traceable(run_type=run_type, name=f"Extraction Agent: {agent_name}")
        def trace_call():
            return self._run_single_extractor(agent_name, sentences)

        return trace_call()

    def _handle_extractor_failure(self, agent_name: str, sentences: List[dict]) -> List[EntityMentionModel]:
        """Handles extractor error fallback logic using fallback settings from config."""
        fallback_rule = self.fallback_routes.get(
            agent_name, {"on_failure": "log_and_continue"})
        strategy = fallback_rule.get("on_failure", "log_and_continue")

        logger.warning(
            f"Handling failure for agent '{agent_name}' with strategy '{strategy}'")

        if strategy == "log_and_continue":
            return []
        elif strategy in ("scispacy", "biobert", "groq", "dosage_frequency"):
            # Execute the designated fallback extractor
            logger.info(
                f"Executing fallback agent '{strategy}' for failed agent '{agent_name}'")
            try:
                return self._run_single_extractor_trace(strategy, sentences)
            except Exception as e:
                logger.error(f"Fallback agent '{strategy}' also failed: {e}")
                return []
        else:
            return []
