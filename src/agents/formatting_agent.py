from typing import Any, Dict
from src.models.pipeline_state import PipelineState
from src.monitoring.logger import logger, set_log_context


class FormattingAgent:
    def __init__(self, config: dict):
        self.config = config or {}
        self.include_confidence_scores = self.config.get(
            "include_confidence_scores", True)
        self.include_source_agents = self.config.get(
            "include_source_agents", True)

    def process(self, state: PipelineState) -> Dict[str, Any]:
        """
        Formats final pipeline results into a structured output dictionary.
        Updates state status to COMPLETED.
        """
        set_log_context(state.session_id, "formatting_agent")
        logger.info("Formatting pipeline output")

        entities_output = []
        for ent in state.final_entities:
            ent_data = {
                "text": ent.text,
                "type": ent.type,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
            }

            if self.include_confidence_scores:
                ent_data["confidence"] = round(ent.confidence, 4)

            if self.include_source_agents:
                ent_data["source_agents"] = ent.source_agents

            if ent.canonical_id:
                ent_data["canonical_id"] = ent.canonical_id
                ent_data["canonical_name"] = ent.canonical_name

            ent_data["needs_review"] = ent.needs_review

            entities_output.append(ent_data)

        state.status = "COMPLETED"

        output = {
            "session_id": state.session_id,
            "document_id": state.document_id,
            "status": state.status,
            "entities": entities_output,
            "metadata": state.metadata
        }

        logger.info(
            f"Formatting complete. Formatted {len(entities_output)} entities.")
        return output
