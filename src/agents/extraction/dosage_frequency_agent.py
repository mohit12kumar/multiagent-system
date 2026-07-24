import re
from typing import List
from src.models.entity import EntityMentionModel

# Regex patterns for medication dosages
DOSAGE_PATTERNS = [
    # 500 mg, 10ml, 2.5 mcg, 2 tablets, 100 units
    re.compile(r'\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|tablet|tablets|capsule|capsules|unit|units|u|mg/ml|mg/dl)\b', re.IGNORECASE)
]

# Regex patterns for medication administration frequency
FREQUENCY_PATTERNS = [
    # twice daily, once a day, three times daily
    re.compile(
        r'\b(?:once|twice|three times|four times)\s+(?:daily|a day|weekly|a week)\b', re.IGNORECASE),
    # daily, every day, every 8 hours, at bedtime
    re.compile(r'\b(?<!once\s)(?<!twice\s)(?<!times\s)(?:daily|every day|at bedtime|every\s+\d+\s*(?:hours|hrs|hour|hr))\b', re.IGNORECASE),
    # Latin medical abbreviations (q.d., b.i.d., t.i.d., q.i.d., q.h.s., q8h)
    re.compile(
        r'\b(?:q\.d\.|b\.i\.d\.|t\.i\.d\.|q\.i\.d\.|q\.h\.s\.|q\s*\d+\s*h|bid|tid|qid|qhs)\b', re.IGNORECASE)
]


class DosageFrequencyAgent:
    def __init__(self, config: dict):
        self.config = config or {}
        self.confidence_threshold = self.config.get(
            "confidence_threshold", 0.90)

    def extract(self, sentences: List[dict]) -> List[EntityMentionModel]:
        """
        Runs regex extraction to find dosages and administration frequencies.
        """
        extractions = []

        for sent in sentences:
            sent_text = sent["text"]
            sent_start = sent["start_char"]

            # Extract Dosages
            for pattern in DOSAGE_PATTERNS:
                for match in pattern.finditer(sent_text):
                    start = sent_start + match.start()
                    end = sent_start + match.end()
                    extractions.append(EntityMentionModel(
                        text=match.group(),
                        type="DOSAGE",
                        start_char=start,
                        end_char=end,
                        confidence=self.confidence_threshold,
                        source_agents=["dosage_frequency"]
                    ))

            # Extract Frequencies
            for pattern in FREQUENCY_PATTERNS:
                for match in pattern.finditer(sent_text):
                    start = sent_start + match.start()
                    end = sent_start + match.end()
                    extractions.append(EntityMentionModel(
                        text=match.group(),
                        type="FREQUENCY",
                        start_char=start,
                        end_char=end,
                        confidence=self.confidence_threshold,
                        source_agents=["dosage_frequency"]
                    ))

        return extractions
