import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.models.pipeline_state import PipelineState
from backend.database.mysql_store import MySQLStore
from backend.services.chroma_service import ChromaService

# Import 13 agents
from backend.agents.phi_redaction_agent import PHIRedactionAgent
from backend.agents.scispacy_agent import SciSpaCyAgent
from backend.agents.biobert_agent import BioBERTAgent
from backend.agents.spacy_agent import SpaCyAgent
from backend.agents.regex_agent import RegexAgent
from backend.agents.llm_clinical_agent import LLMClinicalAgent
from backend.agents.aggregation_agent import AggregationAgent
from backend.agents.validation_agent import ValidationAgent
from backend.agents.relation_extraction_agent import RelationExtractionAgent
from backend.agents.medication_validation_agent import MedicationValidationAgent
from backend.agents.disambiguation_agent import DisambiguationAgent
from backend.agents.formatting_agent import FormattingAgent
from backend.agents.human_review_agent import HumanReviewAgent
from backend.agents.spell_correction_agent import MedicalSpellCorrectionAgent
from backend.agents.abbreviation_agent import MedicalAbbreviationAgent
from backend.agents.section_detector_agent import SectionDetectorAgent

from backend.orchestrator.router import Router
from src.monitoring.logger import logger, set_log_context


class Coordinator:
    def __init__(self, db_session: Optional[Session] = None):
        if db_session is None:
            from backend.database.connection import SessionLocal
            db_session = SessionLocal()
        self.db = db_session
        self.mysql_store = MySQLStore(db_session)
        self.chroma_service = ChromaService()

        # Instantiate 13 agents
        self.phi_redaction_agent = PHIRedactionAgent()
        self.scispacy_agent = SciSpaCyAgent()
        self.biobert_agent = BioBERTAgent()
        self.spacy_agent = SpaCyAgent()
        self.regex_agent = RegexAgent()
        self.llm_clinical_agent = LLMClinicalAgent()
        self.aggregation_agent = AggregationAgent()
        self.validation_agent = ValidationAgent()
        self.relation_extraction_agent = RelationExtractionAgent()
        self.medication_validation_agent = MedicationValidationAgent()
        self.disambiguation_agent = DisambiguationAgent(chroma_service=self.chroma_service, mysql_store=self.mysql_store)
        self.formatting_agent = FormattingAgent()
        self.human_review_agent = HumanReviewAgent(mysql_store=self.mysql_store)
        self.spell_correction_agent = MedicalSpellCorrectionAgent()
        self.abbreviation_agent = MedicalAbbreviationAgent()
        self.section_detector_agent = SectionDetectorAgent()
        self.router = Router()

    def set_db(self, db_session: Session):
        """Attaches active request DB session to coordinator and dependent agents."""
        self.db = db_session
        if self.mysql_store is None:
            self.mysql_store = MySQLStore(db_session)
        else:
            self.mysql_store.db = db_session
        if hasattr(self, 'disambiguation_agent'):
            self.disambiguation_agent.mysql_store = self.mysql_store
        if hasattr(self, 'human_review_agent'):
            self.human_review_agent.mysql_store = self.mysql_store

    def run_pipeline(self, document_content: str, user_id: Optional[str] = None, doc_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        doc_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        set_log_context(session_id, "coordinator")
        logger.info(f"Initiating pipeline session {session_id} for clinical note")

        # 1. Create Document & Session in MySQL
        self.mysql_store.create_document(doc_id, document_content, doc_metadata, user_id=user_id)
        self.mysql_store.create_session(session_id, doc_id)

        # Preprocessing: Expand abbreviations and check spelling
        processed_content = document_content
        try:
            processed_content = self.abbreviation_agent.expand_abbreviations(processed_content)
            processed_content = self.spell_correction_agent.correct_phrase(processed_content)
            logger.info("Clinical text preprocessing (spelling & abbreviation expansion) completed successfully.")
        except Exception as e:
            logger.warning(f"Clinical text preprocessing failed (non-fatal): {e}")

        # Detect clinical document sections
        sections = []
        try:
            sections = self.section_detector_agent.detect_sections(processed_content)
            logger.info(f"Detected {len(sections)} clinical document sections.")
        except Exception as e:
            logger.warning(f"Clinical section detection failed (non-fatal): {e}")

        state = PipelineState(
            session_id=session_id,
            document_id=doc_id,
            user_id=user_id,
            text=processed_content,
            status="IN_PROGRESS",
            current_stage="PHI_REDACTION",
            metadata=doc_metadata or {}
        )
        state.metadata["sections"] = sections

        failed_stages = []

        try:
            # Stage 1: PHI Redaction
            self.mysql_store.update_session(session_id, "IN_PROGRESS", "PHI_REDACTION")
            state = self.phi_redaction_agent.process(state)
            if state.phi_redactions:
                self.mysql_store.save_phi_audit(session_id, state.phi_redactions)
        except Exception as e:
            logger.warning(f"PHI Redaction failed (non-fatal): {e}")
            failed_stages.append("PHI_REDACTION")

        try:
            # Stage 2: NLP SpaCy Segmentation & POS tagging
            sentences, pos_tags = self.spacy_agent.process_nlp(state.text)
            state.sentences = sentences
            state.pos_tags = pos_tags
        except Exception as e:
            logger.warning(f"SpaCy NLP failed (non-fatal): {e}")
            state.sentences = [{"text": state.text, "start": 0, "end": len(state.text)}]
            failed_stages.append("NLP_SEGMENTATION")

        try:
            # Stage 3: Parallel Entity Extractions
            self.mysql_store.update_session(session_id, "IN_PROGRESS", "EXTRACTION")
            active_agents = self.router.route(state)
            raw_extractions = self._execute_extraction_agents(active_agents, state.sentences)
            state.raw_extractions = raw_extractions
        except Exception as e:
            logger.warning(f"Extraction stage failed (non-fatal): {e}")
            state.raw_extractions = {}
            failed_stages.append("EXTRACTION")

        try:
            # Stage 4: Consensus Aggregation & Voting
            self.mysql_store.update_session(session_id, "IN_PROGRESS", "AGGREGATION")
            state = self.aggregation_agent.process(state)
        except Exception as e:
            logger.warning(f"Aggregation failed (non-fatal): {e}")
            failed_stages.append("AGGREGATION")

        try:
            # Stage 5: Taxonomy & Threshold Validation
            self.mysql_store.update_session(session_id, "IN_PROGRESS", "VALIDATION")
            state = self.validation_agent.process(state)
        except Exception as e:
            logger.warning(f"Validation failed (non-fatal): {e}")
            failed_stages.append("VALIDATION")

        try:
            # Stage 6: Semantic Relation Extraction
            self.mysql_store.update_session(session_id, "IN_PROGRESS", "RELATION_EXTRACTION")
            state = self.relation_extraction_agent.process(state)
        except Exception as e:
            logger.warning(f"Relation extraction failed (non-fatal): {e}")
            failed_stages.append("RELATION_EXTRACTION")

        try:
            # Stage 7: Medication Validation
            self.mysql_store.update_session(session_id, "IN_PROGRESS", "MEDICATION_VALIDATION")
            state = self.medication_validation_agent.process(state)
        except Exception as e:
            logger.warning(f"Medication validation failed (non-fatal): {e}")
            failed_stages.append("MEDICATION_VALIDATION")

        try:
            # Stage 8: ChromaDB Vector Terminology Disambiguation
            self.mysql_store.update_session(session_id, "IN_PROGRESS", "DISAMBIGUATION")
            state = self.disambiguation_agent.process(state)
        except Exception as e:
            logger.warning(f"Disambiguation failed (non-fatal): {e}")
            failed_stages.append("DISAMBIGUATION")

        try:
            # Stage 9: Output Formatting
            self.mysql_store.update_session(session_id, "IN_PROGRESS", "FORMATTING")
            output = self.formatting_agent.process(state)
        except Exception as e:
            logger.error(f"Formatting failed: {e}")
            output = {
                "session_id": session_id,
                "document_id": doc_id,
                "status": "PARTIAL_FAILURE",
                "patient_summary": [],
                "patient_message": "Processing completed with some agent errors."
            }
            failed_stages.append("FORMATTING")

        try:
            # Stage 10: Persist Mentions, Relations & Patient History
            raw_mentions = [
                {
                    "text": ent.text,
                    "type": ent.type,
                    "start_char": ent.start_char,
                    "end_char": ent.end_char,
                    "confidence": ent.confidence,
                    "source_agents": ent.source_agents,
                    "canonical_id": ent.canonical_id,
                    "needs_review": ent.needs_review
                }
                for ent in state.final_entities
            ]
            self.mysql_store.save_entity_mentions(session_id, doc_id, raw_mentions)
            self.mysql_store.save_disease_relations(session_id, state.disease_relations)
            self.mysql_store.save_medication_relations(session_id, state.medication_relations)

            eff_user_id = user_id or "anonymous_patient"
            self.mysql_store.save_patient_history(eff_user_id, session_id, output.get("patient_summary", []))

            # Always create a session-level review entry so the doctor can see every
            # patient-submitted note in the review queue (even if all entities were high-confidence)
            self.mysql_store.save_session_review_entry(session_id, user_id=eff_user_id)
        except Exception as e:
            logger.error(f"Persistence stage failed: {e}", exc_info=True)
            failed_stages.append("PERSISTENCE")

        # Final status
        if failed_stages:
            logger.warning(f"Pipeline completed with partial failures in: {failed_stages}")
            output["failed_stages"] = failed_stages

        final_status = "COMPLETED" if not failed_stages else "PARTIAL_SUCCESS"
        self.mysql_store.update_session(session_id, final_status, "COMPLETED")
        return output


    def _execute_extraction_agents(self, active_agents: List[str], sentences: List[dict], full_text: Optional[str] = None) -> Dict[str, List[Any]]:
        raw_extractions = {}
        with ThreadPoolExecutor(max_workers=max(1, len(active_agents))) as executor:
            future_to_agent = {
                executor.submit(self._run_extractor, agent_name, sentences, full_text): agent_name
                for agent_name in active_agents
            }
            for future in as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    raw_extractions[agent_name] = future.result()
                except Exception as e:
                    logger.error(f"Agent '{agent_name}' failed: {e}")
                    raw_extractions[agent_name] = []
        return raw_extractions

    def _run_extractor(self, agent_name: str, sentences: List[dict], full_text: Optional[str] = None) -> List[Any]:
        if agent_name == "scispacy":
            return self.scispacy_agent.extract(sentences, full_text=full_text)
        elif agent_name == "biobert":
            return self.biobert_agent.extract(sentences, full_text=full_text)
        elif agent_name == "regex":
            return self.regex_agent.extract(sentences, full_text=full_text)
        elif agent_name == "local_llm":
            return self.llm_clinical_agent.extract(sentences, full_text=full_text)
        return []
