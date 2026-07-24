import re
import os
import csv
from typing import List
from src.models.entity import EntityMentionModel
from src.monitoring.logger import logger


class ScispacyAgent:
    def __init__(self, config: dict):
        self.config = config or {}
        self.model_name = self.config.get("model_name", "en_core_sci_sm")
        self.confidence_threshold = self.config.get(
            "confidence_threshold", 0.70)
        self.supported_entities = self.config.get(
            "supported_entities", ["DISEASE", "DRUG", "ANATOMY"])

        self.nlp = None
        self.has_scispacy = False

        # Load local gazetteer fallbacks
        BASE_DIR = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.gazetteers = {
            "DRUG": os.path.join(BASE_DIR, "data", "gazetteers", "drug_list.csv"),
            "DISEASE": os.path.join(BASE_DIR, "data", "gazetteers", "disease_list.csv"),
            "ANATOMY": os.path.join(BASE_DIR, "data", "gazetteers", "anatomy_terms.csv")
        }

        # Try loading scispacy
        self._load_scispacy()

    def _load_scispacy(self) -> None:
        """Attempts to load SciSpacy library and model."""
        try:
            import spacy
            logger.info(f"Loading SciSpacy model: {self.model_name}")
            self.nlp = spacy.load(self.model_name)
            self.has_scispacy = True
            logger.info("Successfully loaded SciSpacy NLP module")
        except OSError:
            logger.warning(
                f"SciSpacy model '{self.model_name}' not found. Falling back to local gazetteer lookups.")
            self.has_scispacy = False
        except Exception as e:
            logger.warning(
                f"SciSpacy library load failed: {e}. Falling back to local gazetteer lookups.")
            self.has_scispacy = False

    def extract(self, sentences: List[dict]) -> List[EntityMentionModel]:
        """
        Extracts medical entities from sentences.
        If SciSpacy is loaded, it executes inference. Otherwise, it runs local CSV matches.
        """
        if self.has_scispacy and self.nlp:
            return self._extract_scispacy(sentences)
        else:
            return self._extract_gazetteer(sentences)

    def _extract_scispacy(self, sentences: List[dict]) -> List[EntityMentionModel]:
        extractions = []
        for sent in sentences:
            sent_text = sent["text"]
            sent_start = sent["start_char"]
            try:
                doc = self.nlp(sent_text)
                for ent in doc.ents:
                    # SciSpacy uses specific labels like 'ENTITY' or specialized categories
                    # We map them or accept them based on config
                    start_char = sent_start + ent.start_char
                    end_char = sent_start + ent.end_char

                    # Basic mapping heuristic for scispacy output
                    ent_label = "DISEASE"  # Fallback category
                    label_upper = ent.label_.upper()
                    if "CHEMICAL" in label_upper or "DRUG" in label_upper:
                        ent_label = "DRUG"
                    elif "ANATOMY" in label_upper or "ORGAN" in label_upper:
                        ent_label = "ANATOMY"

                    if ent_label in self.supported_entities:
                        extractions.append(EntityMentionModel(
                            text=ent.text,
                            type=ent_label,
                            start_char=start_char,
                            end_char=end_char,
                            confidence=self.confidence_threshold,
                            source_agents=["scispacy"]
                        ))
            except Exception as e:
                logger.error(f"SciSpacy inference failed: {e}")
        return extractions

    def _extract_gazetteer(self, sentences: List[dict]) -> List[EntityMentionModel]:
        """Runs offline substring matches against CSV gazetteers to extract terms."""
        extractions = []

        # Load CSV terms into dictionaries
        terms_by_type = {}
        for ent_type, file_path in self.gazetteers.items():
            if ent_type not in self.supported_entities:
                continue
            if not os.path.exists(file_path):
                continue

            terms = set()
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        terms.add(row["name"].strip())
                terms_by_type[ent_type] = terms
            except Exception as e:
                logger.error(f"Failed to read gazetteer {file_path}: {e}")

        # Scan text for matching words
        for sent in sentences:
            sent_text = sent["text"]
            sent_start = sent["start_char"]

            for ent_type, terms in terms_by_type.items():
                for term in terms:
                    # Case insensitive lookup
                    # Ensure word boundary matches to prevent partial matching (e.g. 'in' in 'insulin')
                    pattern = r'\b' + re.escape(term) + r'\b'
                    for match in re.finditer(pattern, sent_text, re.IGNORECASE):
                        start_char = sent_start + match.start()
                        end_char = sent_start + match.end()
                        exact_term = sent_text[match.start():match.end()]

                        extractions.append(EntityMentionModel(
                            text=exact_term,
                            type=ent_type,
                            start_char=start_char,
                            end_char=end_char,
                            # Slightly lower confidence for gazetteer
                            confidence=self.confidence_threshold - 0.05,
                            source_agents=["scispacy"]
                        ))

        return extractions
