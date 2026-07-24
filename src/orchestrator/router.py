import os
import yaml
from typing import List
from src.models.pipeline_state import PipelineState
from src.monitoring.logger import logger


class Router:
    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        PIPELINE_PATH = os.path.join(BASE_DIR, "config", "pipeline.yaml")
        AGENTS_PATH = os.path.join(BASE_DIR, "config", "agents.yaml")

        self.active_extractors = ["scispacy",
                                  "biobert", "ollama", "dosage_frequency"]
        self.max_llm_calls = 5

        if os.path.exists(PIPELINE_PATH):
            try:
                with open(PIPELINE_PATH, "r") as f:
                    config = yaml.safe_load(f)
                    pipeline_cfg = config.get("pipeline", {})
                    self.active_extractors = pipeline_cfg.get(
                        "active_extractors", self.active_extractors)
            except Exception as e:
                logger.error(f"Failed to load pipeline router config: {e}")

        if os.path.exists(AGENTS_PATH):
            try:
                with open(AGENTS_PATH, "r") as f:
                    config = yaml.safe_load(f)
                    ollama_cfg = config.get("ollama_agent", {})
                    self.max_llm_calls = ollama_cfg.get(
                        "max_llm_calls_per_document", 5)
            except Exception as e:
                logger.error(f"Failed to load agents config in router: {e}")

    def route(self, state: PipelineState) -> List[str]:
        """
        Determines the list of active extraction agents.
        Enforces maximum LLM execution limits if document contains too many sentences.
        """
        active = list(self.active_extractors)

        # Enforce LLM call ceiling to manage latency
        if "ollama" in active:
            sentence_count = len(state.sentences)
            if sentence_count > self.max_llm_calls:
                logger.warning(
                    f"Document contains {sentence_count} sentences, exceeding LLM cap of {self.max_llm_calls}. "
                    "Ollama agent will be restricted to the first 5 sentences."
                )

        logger.info(
            f"Routed medical document {state.document_id} to extractors: {active}")
        return active
