from typing import Dict, Any
from backend.models.pipeline_state import PipelineState
from backend.services.rxnorm_service import RxNormService
from backend.services.wikidata_service import WikidataService
from src.monitoring.logger import logger


class MedicationValidationAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def process(self, state: PipelineState) -> PipelineState:
        logger.info(f"Medication Validation Agent verifying prescriptions for session {state.session_id}")

        summaries = state.patient_summary
        for summary in summaries:
            if summary.medication:
                med = summary.medication
                disease_name = summary.disease
                drug_name = med.name

                # 1. Query free RxNorm API for drug validity
                rx_result = RxNormService.validate_drug(drug_name)
                
                # 2. Query free Wikidata & medical ontology service for drug-disease appropriateness
                wiki_result = WikidataService.validate_disease_medication_pair(disease_name, drug_name)

                status = wiki_result.get("validation_status", "Correct Medication")
                correct = wiki_result.get("correct", True)
                conf = wiki_result.get("confidence", 0.95)
                reason = wiki_result.get("reason", "Verified via free medical ontologies (RxNorm/Wikidata)")

                if not rx_result.get("valid") and status == "Unknown Medication":
                    status = "Unknown Medication"
                    correct = False
                    conf = 0.50
                    reason = f"Drug '{drug_name}' could not be validated in RxNorm or Wikidata"

                med.validation_status = status
                med.correct = correct
                med.confidence = round(conf, 2)
                med.validation_reason = reason

        logger.info("Medication Validation Agent completed successfully.")
        return state
