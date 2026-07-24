import spacy
import spacy.cli
from typing import List
from src.models.entity import EntityMentionModel
from src.monitoring.logger import logger


class SpacyAgent:
    def __init__(self, config: dict):
        self.config = config or {}
        self.model_name = self.config.get("model_name", "en_core_web_sm")
        self.confidence_threshold = self.config.get(
            "confidence_threshold", 0.65)
        self.supported_entities = self.config.get(
            "supported_entities", ["PERSON", "ORG", "GPE", "LOC", "DATE", "TIME"])
        self.nlp = None
        self._load_model()

    def _load_model(self) -> None:
        """Loads SpaCy model, downloading it if missing."""
        try:
            logger.info(f"Loading SpaCy model: {self.model_name}")
            self.nlp = spacy.load(self.model_name)
        except OSError:
            logger.warning(
                f"SpaCy model '{self.model_name}' not found. Attempting auto-download.")
            try:
                spacy.cli.download(self.model_name)
                self.nlp = spacy.load(self.model_name)
                logger.info(
                    f"Successfully downloaded and loaded {self.model_name}")
            except BaseException as e:
                logger.error(f"Failed to auto-download SpaCy model: {e}")
                self.nlp = None

    def extract(self, sentences: List[dict]) -> List[EntityMentionModel]:
        """
        Extracts entities from segmented sentences.
        Maps entity offsets back to document level.
        """
        if not self.nlp:
            logger.error("SpaCy NLP model not loaded. Skipping extraction.")
            return []

        extractions = []
        for sent in sentences:
            sent_text = sent["text"]
            sent_start = sent["start_char"]

            try:
                doc = self.nlp(sent_text)
                for ent in doc.ents:
                    if ent.label_ in self.supported_entities:
                        # Map token bounds
                        start_char = sent_start + ent.start_char
                        end_char = sent_start + ent.end_char

                        extractions.append(EntityMentionModel(
                            text=ent.text,
                            type=ent.label_,
                            start_char=start_char,
                            end_char=end_char,
                            confidence=self.confidence_threshold,  # SpaCy rule/statistical baseline conf
                            source_agents=["spacy"]
                        ))
            except Exception as e:
                logger.error(
                    f"SpaCy extraction failed on sentence '{sent_text}': {e}")

        return extractions
