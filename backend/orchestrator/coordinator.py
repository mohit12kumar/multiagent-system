import uuid
import copy
import time
import gc
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.models.pipeline_state import PipelineState
from backend.database.mysql_store import MySQLStore
from backend.services.chroma_service import ChromaService
from backend.core.agent_context import AgentContext
from backend.core.model_registry import ModelRegistry
from backend.core.metrics import metrics_collector
from backend.core.prompt_budget import truncate_text_to_token_budget

# Import all agents
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
from backend.agents.medication_parser import MedicationParserAgent

from backend.orchestrator.router import Router
from src.monitoring.logger import logger, set_log_context

_log = logging.getLogger(__name__)
_STAGE_TIMEOUT = 30


class Coordinator:
    """
    Stateless Clinical NLP Pipeline Coordinator with AgentContext isolation,
    garbage collection, metrics tracking, and ModelRegistry provenance.
    """

    def __init__(self):
        self.chroma_service = ChromaService()

        # Instantiate all agents (model weights loaded here, once)
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
        self.disambiguation_agent = DisambiguationAgent(chroma_service=self.chroma_service)
        self.formatting_agent = FormattingAgent()
        self.human_review_agent = HumanReviewAgent()
        self.spell_correction_agent = MedicalSpellCorrectionAgent()
        self.abbreviation_agent = MedicalAbbreviationAgent()
        self.section_detector_agent = SectionDetectorAgent()
        self.router = Router()

        _log.info("Coordinator: all agents initialised successfully.")

    def run_pipeline(
        self,
        document_content: str,
        db: Session,
        user_id: Optional[str] = None,
        doc_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full clinical NLP pipeline for one request.
        """
        start_time = time.time()
        doc_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        set_log_context(session_id, "coordinator")

        # Create request-isolated AgentContext
        agent_ctx = AgentContext(
            session_id=session_id,
            document_id=doc_id,
            user_id=user_id,
            text=document_content,
            metadata=doc_metadata or {}
        )
        logger.info(f"Pipeline initiated | session={session_id} | request_id={agent_ctx.request_id}")

        mysql_store = MySQLStore(db)
        disambiguation_agent = DisambiguationAgent(
            chroma_service=self.chroma_service,
            mysql_store=mysql_store
        )

        try:
            mysql_store.create_document(doc_id, document_content, doc_metadata, user_id=user_id)
            mysql_store.create_session(session_id, doc_id)
        except Exception as e:
            logger.error(f"[{session_id}] Failed to create initial DB records: {e}", exc_info=True)
            raise

        failed_stages: List[str] = []
        output: Dict[str, Any] = {}

        # ── Step 2: Text Preprocessing & Budgeting ───────────────────────────
        processed_content = truncate_text_to_token_budget(document_content)
        try:
            t0 = time.time()
            processed_content = self.abbreviation_agent.expand_abbreviations(processed_content)
            processed_content = self.spell_correction_agent.correct_phrase(processed_content)
            metrics_collector.record_stage("PREPROCESSING", time.time() - t0, True)
        except Exception as e:
            logger.warning(f"[{session_id}] Text preprocessing failed (non-fatal): {e}")

        # ── Step 3: Section Detection ─────────────────────────────────────────
        sections: List[Any] = []
        try:
            t0 = time.time()
            sections = self.section_detector_agent.detect_sections(processed_content)
            metrics_collector.record_stage("SECTION_DETECTION", time.time() - t0, True)
        except Exception as e:
            logger.warning(f"[{session_id}] Section detection failed (non-fatal): {e}")

        # ── Build PipelineState ───────────────────────────────────────────────
        state = PipelineState(
            session_id=session_id,
            document_id=doc_id,
            user_id=user_id,
            text=processed_content,
            status="IN_PROGRESS",
            current_stage="PHI_REDACTION",
            metadata={**(doc_metadata or {}), "sections": sections, "request_id": agent_ctx.request_id}
        )

        try:
            # ── Stage 1: PHI Redaction ────────────────────────────────────────
            try:
                t0 = time.time()
                mysql_store.update_session(session_id, "IN_PROGRESS", "PHI_REDACTION")
                state = self.phi_redaction_agent.process(state)
                if state.phi_redactions:
                    mysql_store.save_phi_audit(session_id, state.phi_redactions)
                metrics_collector.record_stage("PHI_REDACTION", time.time() - t0, True)
            except Exception as e:
                logger.warning(f"[{session_id}] PHI Redaction failed (non-fatal): {e}")
                failed_stages.append("PHI_REDACTION")
                metrics_collector.record_stage("PHI_REDACTION", 0, False)

            # ── Stage 2: NLP Segmentation ─────────────────────────────────────
            try:
                t0 = time.time()
                sentences, pos_tags = self.spacy_agent.process_nlp(state.text)
                state.sentences = sentences
                state.pos_tags = pos_tags
                metrics_collector.record_stage("NLP_SEGMENTATION", time.time() - t0, True)
            except Exception as e:
                logger.warning(f"[{session_id}] SpaCy NLP failed (non-fatal): {e}")
                state.sentences = [{"text": state.text, "start": 0, "end": len(state.text)}]
                failed_stages.append("NLP_SEGMENTATION")
                metrics_collector.record_stage("NLP_SEGMENTATION", 0, False)

            # ── Stage 3: Parallel Entity Extraction ───────────────────────────
            try:
                t0 = time.time()
                mysql_store.update_session(session_id, "IN_PROGRESS", "EXTRACTION")
                active_agents = self.router.route(state)
                sentences_snapshot = copy.deepcopy(state.sentences)
                raw_extractions = self._execute_extraction_agents(
                    active_agents, sentences_snapshot, full_text=state.text
                )
                state.raw_extractions = raw_extractions

                for _agent_name, mentions in state.raw_extractions.items():
                    for mention in mentions:
                        for sec in sections:
                            sec_start = sec.get("start_char", 0)
                            sec_end = sec.get("end_char", len(state.text))
                            if sec_start <= mention.start_char <= sec_end:
                                mention.section = sec.get("name", "GENERAL")
                                break
                metrics_collector.record_stage("EXTRACTION", time.time() - t0, True)
            except Exception as e:
                logger.warning(f"[{session_id}] Extraction failed (non-fatal): {e}")
                state.raw_extractions = {}
                failed_stages.append("EXTRACTION")
                metrics_collector.record_stage("EXTRACTION", 0, False)

            # ── Stage 4: Consensus Aggregation ───────────────────────────────
            try:
                t0 = time.time()
                mysql_store.update_session(session_id, "IN_PROGRESS", "AGGREGATION")
                state = self.aggregation_agent.process(state)
                metrics_collector.record_stage("AGGREGATION", time.time() - t0, True)
            except Exception as e:
                logger.warning(f"[{session_id}] Aggregation failed (non-fatal): {e}")
                failed_stages.append("AGGREGATION")
                metrics_collector.record_stage("AGGREGATION", 0, False)

            # ── Stage 5: Taxonomy Validation ─────────────────────────────────
            try:
                t0 = time.time()
                mysql_store.update_session(session_id, "IN_PROGRESS", "VALIDATION")
                state = self.validation_agent.process(state)
                metrics_collector.record_stage("VALIDATION", time.time() - t0, True)
            except Exception as e:
                logger.warning(f"[{session_id}] Validation failed (non-fatal): {e}")
                failed_stages.append("VALIDATION")
                metrics_collector.record_stage("VALIDATION", 0, False)

            # ── Stage 5.5: Universal Medication Parsing ───────────────────────
            try:
                t0 = time.time()
                parsed_prescriptions = MedicationParserAgent.parse_text(state.text)
                state.metadata["parsed_prescriptions"] = parsed_prescriptions
                metrics_collector.record_stage("MEDICATION_PARSER", time.time() - t0, True)
            except Exception as e:
                logger.warning(f"[{session_id}] Universal Medication Parser failed (non-fatal): {e}")

            # ── Stage 6: Relation Extraction ─────────────────────────────────
            try:
                t0 = time.time()
                mysql_store.update_session(session_id, "IN_PROGRESS", "RELATION_EXTRACTION")
                state = self.relation_extraction_agent.process(state)
                metrics_collector.record_stage("RELATION_EXTRACTION", time.time() - t0, True)
            except Exception as e:
                logger.warning(f"[{session_id}] Relation extraction failed (non-fatal): {e}")
                failed_stages.append("RELATION_EXTRACTION")
                metrics_collector.record_stage("RELATION_EXTRACTION", 0, False)

            # ── Stage 7: Medication Validation ───────────────────────────────
            try:
                t0 = time.time()
                mysql_store.update_session(session_id, "IN_PROGRESS", "MEDICATION_VALIDATION")
                state = self.medication_validation_agent.process(state)
                metrics_collector.record_stage("MEDICATION_VALIDATION", time.time() - t0, True)
            except Exception as e:
                logger.warning(f"[{session_id}] Medication validation failed (non-fatal): {e}")
                failed_stages.append("MEDICATION_VALIDATION")
                metrics_collector.record_stage("MEDICATION_VALIDATION", 0, False)

            # ── Stage 8: Disambiguation ───────────────────────────────────────
            try:
                t0 = time.time()
                mysql_store.update_session(session_id, "IN_PROGRESS", "DISAMBIGUATION")
                state = disambiguation_agent.process(state)
                metrics_collector.record_stage("DISAMBIGUATION", time.time() - t0, True)
            except Exception as e:
                logger.warning(f"[{session_id}] Disambiguation failed (non-fatal): {e}")
                failed_stages.append("DISAMBIGUATION")
                metrics_collector.record_stage("DISAMBIGUATION", 0, False)

            # ── Stage 9: Output Formatting ────────────────────────────────────
            try:
                t0 = time.time()
                mysql_store.update_session(session_id, "IN_PROGRESS", "FORMATTING")
                output = self.formatting_agent.process(state)
                metrics_collector.record_stage("FORMATTING", time.time() - t0, True)
            except Exception as e:
                logger.error(f"[{session_id}] Formatting failed: {e}")
                output = {
                    "session_id": session_id,
                    "document_id": doc_id,
                    "status": "PARTIAL_FAILURE",
                    "patient_summary": [],
                    "patient_message": "Processing completed with some agent errors.",
                }
                failed_stages.append("FORMATTING")
                metrics_collector.record_stage("FORMATTING", 0, False)

            # Stamp ModelRegistry version provenance into pipeline output
            output["model_versions"] = ModelRegistry.get_version_info()
            output["request_id"] = agent_ctx.request_id

            # ── Stage 10: Atomic Persistence ─────────────────────────────────
            try:
                raw_mentions = [
                    {
                        "text": ent.text,
                        "type": ent.type,
                        "start_char": ent.start_char,
                        "end_char": ent.end_char,
                        "confidence": ent.confidence,
                        "source_agents": ent.source_agents,
                        "canonical_id": ent.canonical_id,
                        "needs_review": ent.needs_review,
                    }
                    for ent in state.final_entities
                ]
                eff_user_id = user_id or "anonymous_patient"

                mysql_store.save_pipeline_results(
                    session_id=session_id,
                    doc_id=doc_id,
                    entity_mentions=raw_mentions,
                    disease_relations=state.disease_relations,
                    medication_relations=state.medication_relations,
                    patient_summary=output.get("patient_summary", []),
                    user_id=eff_user_id,
                )
                logger.info(f"[{session_id}] All pipeline results persisted atomically.")
            except Exception as e:
                logger.error(f"[{session_id}] Atomic persistence failed: {e}", exc_info=True)
                failed_stages.append("PERSISTENCE")

            if failed_stages:
                logger.warning(f"[{session_id}] Pipeline completed with partial failures: {failed_stages}")
                output["failed_stages"] = failed_stages

            final_status = "COMPLETED" if not failed_stages else "PARTIAL_SUCCESS"
            mysql_store.update_session(session_id, final_status, "COMPLETED")
            duration = time.time() - start_time
            metrics_collector.record_pipeline(duration, len(failed_stages) == 0)
            logger.info(f"[{session_id}] Pipeline finished | status={final_status} | duration={round(duration, 3)}s")
            return output

        finally:
            # Explicit garbage collection memory cleanup
            del state
            del agent_ctx
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

    def _execute_extraction_agents(
        self,
        active_agents: List[str],
        sentences: List[dict],
        full_text: Optional[str] = None,
    ) -> Dict[str, List[Any]]:
        raw_extractions: Dict[str, List[Any]] = {}
        n_workers = max(1, len(active_agents))

        executor = ThreadPoolExecutor(max_workers=n_workers)
        try:
            future_to_agent = {
                executor.submit(
                    self._run_extractor,
                    agent_name,
                    copy.deepcopy(sentences),
                    full_text,
                ): agent_name
                for agent_name in active_agents
            }
            for future in as_completed(future_to_agent, timeout=_STAGE_TIMEOUT * n_workers):
                agent_name = future_to_agent[future]
                try:
                    raw_extractions[agent_name] = future.result(timeout=_STAGE_TIMEOUT)
                except FuturesTimeoutError:
                    logger.error(f"Agent '{agent_name}' timed out after {_STAGE_TIMEOUT}s")
                    raw_extractions[agent_name] = []
                except Exception as e:
                    logger.error(f"Agent '{agent_name}' raised an exception: {e}")
                    raw_extractions[agent_name] = []
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        return raw_extractions

    def _run_extractor(
        self,
        agent_name: str,
        sentences: List[dict],
        full_text: Optional[str] = None,
    ) -> List[Any]:
        if agent_name == "scispacy":
            return self.scispacy_agent.extract(sentences, full_text=full_text)
        elif agent_name == "biobert":
            return self.biobert_agent.extract(sentences, full_text=full_text)
        elif agent_name == "regex":
            return self.regex_agent.extract(sentences, full_text=full_text)
        elif agent_name == "local_llm":
            return self.llm_clinical_agent.extract(sentences, full_text=full_text)
        return []

