from src.models.pipeline_state import PipelineState
from src.utils.text_cleaning import clean_text
from src.utils.tokenizer import segment_sentences
from src.monitoring.logger import logger, set_log_context


class PreprocessingAgent:
    def __init__(self, config: dict):
        self.config = config or {}
        self.lowercase = self.config.get("lowercase", False)
        self.remove_whitespace = self.config.get(
            "remove_extra_whitespace", True)

    def process(self, state: PipelineState) -> PipelineState:
        """
        Cleans text and segments into sentences.
        """
        set_log_context(state.session_id, "preprocessing_agent")
        logger.info(
            f"Starting text preprocessing for document {state.document_id}")

        try:
            # Clean text
            cleaned_text = clean_text(
                state.text,
                remove_whitespace=self.remove_whitespace,
                normalize=True
            )
            if self.lowercase:
                cleaned_text = cleaned_text.lower()

            state.text = cleaned_text

            # Segment sentences
            sentences = segment_sentences(state.text)
            state.sentences = sentences
            state.current_stage = "EXTRACTION"

            logger.info(
                f"Preprocessing completed. Segmented into {len(sentences)} sentences.")
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}", exc_info=True)
            state.status = "FAILED"
            state.error_message = f"Preprocessing failed: {str(e)}"

        return state
