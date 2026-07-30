import re
from typing import Dict, Any, List, Tuple
from backend.models.pipeline_state import PipelineState
from src.monitoring.logger import logger


class SpaCyAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.agent_name = "spacy"
        self._nlp = None  # Lazy-loaded on first use

    def _factory(self):
        try:
            import spacy
            logger.info("SpaCy model 'en_core_web_sm' loaded into pool worker.")
            return spacy.load("en_core_web_sm")
        except Exception as e:
            logger.warning(f"SpaCy model load failed: {e}")
            return None

    def process_nlp(self, text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Performs sentence segmentation, POS tagging, and dependency parsing."""
        logger.info("SpaCy Agent performing sentence segmentation & parsing")
        sentences = []
        pos_tags = []

        from backend.core.inference_pool import get_model_pool
        pool = get_model_pool("en_core_web_sm", self._factory, pool_size=2)
        with pool.acquire() as nlp_spacy:
            if nlp_spacy:
                try:
                    doc = nlp_spacy(text)
                    for sent in doc.sents:
                        sentences.append({
                            "text": sent.text.strip(),
                            "start_char": sent.start_char,
                            "end_char": sent.end_char
                        })

                    for token in doc:
                        if not token.is_space and not token.is_punct:
                            pos_tags.append({
                                "text": token.text,
                                "pos": token.pos_,
                                "tag": token.tag_,
                                "dep": token.dep_,
                                "head": token.head.text
                            })
                    return sentences, pos_tags
                except Exception as e:
                    logger.warning(f"SpaCy NLP processing error: {e}")

        # Fallback regex sentence segmentation
        raw_sents = re.split(r'(?<=[.!?])\s+', text)
        cursor = 0
        for s in raw_sents:
            s_clean = s.strip()
            if s_clean:
                start = text.find(s_clean, cursor)
                end = start + len(s_clean) if start != -1 else cursor + len(s_clean)
                sentences.append({"text": s_clean, "start_char": start if start != -1 else cursor, "end_char": end})
                cursor = end

        return sentences, pos_tags
