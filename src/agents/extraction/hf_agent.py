from typing import List
from src.models.entity import EntityMentionModel
from src.monitoring.logger import logger


class HfAgent:
    def __init__(self, config: dict):
        self.config = config or {}
        self.model_name = self.config.get(
            "model_name", "dbmdz/bert-large-cased-finetuned-conll03-english")
        self.confidence_threshold = self.config.get(
            "confidence_threshold", 0.80)
        self.supported_entities = self.config.get(
            "supported_entities", ["PER", "ORG", "LOC", "MISC"])
        self.pipeline = None
        self._initialized = False

    def _initialize_pipeline(self) -> None:
        """Launches transformers pipeline on demand."""
        if self._initialized:
            return

        try:
            from transformers import pipeline
            logger.info(
                f"Initializing HF transformers pipeline with model {self.model_name}")
            # Use aggregation_strategy="simple" to auto-merge subword tokens and IOB tags
            self.pipeline = pipeline(
                "ner",
                model=self.model_name,
                aggregation_strategy="simple"
            )
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Hugging Face pipeline: {e}")
            self.pipeline = None
            self._initialized = False

    def extract(self, sentences: List[dict]) -> List[EntityMentionModel]:
        """
        Extracts entities using the HF Transformers model.
        Maps character offsets back to the global document level.
        """
        self._initialize_pipeline()
        if not self.pipeline:
            logger.error(
                "Hugging Face pipeline is unavailable. Skipping HF extraction.")
            return []

        extractions = []
        for sent in sentences:
            sent_text = sent["text"]
            sent_start = sent["start_char"]

            try:
                # Run the pipeline on the sentence
                results = self.pipeline(sent_text)
                for res in results:
                    score = float(res.get("score", 1.0))
                    if score < self.confidence_threshold:
                        continue

                    label = res.get("entity_group")
                    if label in self.supported_entities:
                        # Map character bounds back to the document
                        start_char = sent_start + res.get("start", 0)
                        end_char = sent_start + res.get("end", 0)
                        entity_text = res.get("word")

                        extractions.append(EntityMentionModel(
                            text=entity_text,
                            type=label,
                            start_char=start_char,
                            end_char=end_char,
                            confidence=score,
                            source_agents=["hf"]
                        ))
            except Exception as e:
                logger.error(
                    f"Hugging Face NER failed on sentence: '{sent_text}'. Error: {e}")

        return extractions
