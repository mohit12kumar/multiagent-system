import re
from typing import Dict, Any, List

class ClinicalContextClassifier:
    """Clinical Context Classifier for Negation, Past Medical History, Family History, and Allergies."""

    NEGATION_TERMS = [
        "no", "denies", "denied", "without", "negative for", "absent", "rules out", "ruled out", "no evidence of"
    ]

    PAST_HISTORY_TERMS = [
        "history of", "h/o", "past medical history", "pmh", "previous", "prior", "diagnosed in", "status post", "s/p"
    ]

    FAMILY_HISTORY_TERMS = [
        "family history", "fhx", "father", "mother", "brother", "sister", "maternal", "paternal", "parent"
    ]

    ALLERGY_TERMS = [
        "allergic to", "allergy", "allergies", "reaction to", "nkda", "no known drug allergies"
    ]

    @classmethod
    def get_sentence_for_entity(cls, text: str, start_char: int) -> str:
        if not text or start_char is None:
            return ""
        prev_dot = max(text.rfind(".", 0, start_char), text.rfind("\n", 0, start_char))
        sent_start = 0 if prev_dot == -1 else prev_dot + 1

        next_dot = text.find(".", start_char)
        next_nl = text.find("\n", start_char)
        ends = [p for p in [next_dot, next_nl] if p != -1]
        sent_end = min(ends) if ends else len(text)

        return text[sent_start:sent_end].strip()

    @classmethod
    def classify_context(cls, snippet: str) -> str:
        snippet_low = snippet.lower().strip()

        for term in cls.ALLERGY_TERMS:
            if re.search(r'\b' + re.escape(term) + r'\b', snippet_low):
                return "ALLERGY"

        for term in cls.FAMILY_HISTORY_TERMS:
            if re.search(r'\b' + re.escape(term) + r'\b', snippet_low):
                return "FAMILY_HISTORY"

        for term in cls.PAST_HISTORY_TERMS:
            if re.search(r'\b' + re.escape(term) + r'\b', snippet_low):
                return "PAST_MEDICAL_HISTORY"

        for term in cls.NEGATION_TERMS:
            if re.search(r'\b' + re.escape(term) + r'\b', snippet_low):
                return "NEGATED"

        return "ACTIVE_PRESENTING"

    @classmethod
    def filter_active_entities(cls, text: str, entities: List[Any]) -> Dict[str, List[Any]]:
        active_entities = []
        negated_entities = []
        past_history_entities = []
        family_history_entities = []
        allergies = []

        for ent in entities:
            ent_text = ent.text if hasattr(ent, "text") else str(ent)
            ent_start = getattr(ent, "start_char", 0)

            snippet = cls.get_sentence_for_entity(text, ent_start) if text else ent_text
            context = cls.classify_context(snippet)

            if context == "NEGATED":
                negated_entities.append(ent)
            elif context == "FAMILY_HISTORY":
                family_history_entities.append(ent)
            elif context == "PAST_MEDICAL_HISTORY":
                past_history_entities.append(ent)
            elif context == "ALLERGY":
                allergies.append(ent_text)
            else:
                active_entities.append(ent)

        return {
            "active": active_entities,
            "negated": negated_entities,
            "past_history": past_history_entities,
            "family_history": family_history_entities,
            "allergies": allergies
        }
