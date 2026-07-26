import re
from typing import Dict, Any, List, Optional
from backend.models.entity import EntityMentionModel
from src.monitoring.logger import logger


class SciSpaCyAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.agent_name = "scispacy"
        self._nlp = None  # Lazy-loaded on first use

        # Expanded medical vocabulary rules fallback
        self.biomedical_dictionary = {
            "DISEASE": [
                "hypertension", "high blood pressure", "diabetes", "type 2 diabetes", "type 1 diabetes",
                "asthma", "pneumonia", "bronchitis", "bacterial infection", "viral infection", "infection",
                "depression", "anxiety", "hyperlipidemia", "high cholesterol", "gerd", "acid reflux",
                "arrhythmia", "coronary artery disease", "copd", "migraine", "arthritis", "osteoarthritis",
                "rheumatoid arthritis", "chronic kidney disease", "urinary tract infection", "uti", "anemia"
            ],
            "SYMPTOM": [
                "increased thirst", "frequent urination", "excessive thirst", "excessive urination", "polydipsia", "polyuria", "polyphagia",
                "headache", "dizziness", "chest pain", "shortness of breath", "fever", "chills", "cough",
                "productive cough", "dry cough", "phlegm", "sore throat", "fatigue", "weakness", "nausea",
                "vomiting", "diarrhea", "constipation", "abdominal pain", "joint pain", "muscle pain",
                "swelling", "rash", "itching", "numbness", "tingling", "insomnia", "palpitations"
            ],
            "ANATOMY": [
                "heart", "lungs", "chest", "head", "brain", "liver", "kidney", "stomach",
                "blood vessel", "artery", "joint", "throat", "abdomen", "skin", "muscle", "spine"
            ],
            "PROCEDURE": [
                "electrocardiogram", "ecg", "chest x-ray", "ct scan", "mri", "blood test",
                "biopsy", "endoscopy", "echocardiogram", "ultrasound", "lab test"
            ]
        }

    def _get_nlp(self):
        """Lazy-load SciSpaCy model on first request, not at import time."""
        if self._nlp is None:
            try:
                import spacy
                self._nlp = spacy.load("en_core_sci_sm")
                logger.info("SciSpaCy model 'en_core_sci_sm' loaded successfully.")
            except Exception as e:
                logger.warning(f"SciSpaCy model load failed: {e}")
                self._nlp = False
        return self._nlp if self._nlp is not False else None

    def extract(self, sentences: List[dict], full_text: Optional[str] = None) -> List[EntityMentionModel]:
        logger.info(f"SciSpaCy Agent extracting biomedical entities from {len(sentences)} sentences")
        entities = []
        if not full_text:
            full_text = " ".join([s.get("text", "") for s in sentences]) if sentences else ""

        if not full_text.strip():
            return entities

        # Option A: Model extraction
        nlp_scispacy = self._get_nlp()
        if nlp_scispacy:
            try:
                doc = nlp_scispacy(full_text)
                for ent in doc.ents:
                    etype = "DISEASE" if "disease" in ent.label_.lower() else "SYMPTOM"
                    entities.append(EntityMentionModel(
                        text=ent.text,
                        type=etype,
                        start_char=ent.start_char,
                        end_char=ent.end_char,
                        confidence=0.92,
                        source_agents=[self.agent_name]
                    ))
                if entities:
                    return entities
            except Exception as e:
                logger.warning(f"SciSpaCy model extraction failed: {e}")

        # Option B: High-precision biomedical matcher
        extracted_spans = set()
        for category, terms in self.biomedical_dictionary.items():
            for term in terms:
                for match in re.finditer(r'\b' + re.escape(term) + r'\b', full_text, re.IGNORECASE):
                    span_key = (match.start(), match.end(), category)
                    if span_key not in extracted_spans:
                        extracted_spans.add(span_key)
                        entities.append(EntityMentionModel(
                            text=match.group(0),
                            type=category,
                            start_char=match.start(),
                            end_char=match.end(),
                            confidence=0.90,
                            source_agents=[self.agent_name]
                        ))

        return entities
