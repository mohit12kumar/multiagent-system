import re
from typing import List
from src.models.entity import EntityMentionModel

# Regex patterns for dates
DATE_PATTERNS = [
    # 2026-07-17, 17/07/2026, 07.17.26
    re.compile(r'\b\d{1,4}[-./]\d{1,2}[-./]\d{1,4}\b'),
    # July 17, 2026 or July 17th, 2026
    re.compile(
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?,? \d{4}\b', re.IGNORECASE),
    # 17 July 2026 or 17th of July 2026
    re.compile(
        r'\b\d{1,2}(?:st|nd|rd|th)?(?:\s+of)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b', re.IGNORECASE)
]

# Regex patterns for times
TIME_PATTERNS = [
    # 11:25 AM, 15:30:10
    re.compile(r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b'),
    # 10 AM, 9 PM
    re.compile(r'\b(?<!:)\d{1,2}\s*(?:AM|PM|am|pm)\b', re.IGNORECASE)
]


class DateTimeAgent:
    def __init__(self, config: dict):
        self.config = config or {}
        self.confidence_threshold = self.config.get(
            "confidence_threshold", 0.90)

    def extract(self, sentences: List[dict]) -> List[EntityMentionModel]:
        """
        Runs regex matchers on segmented sentences to find dates and times.
        """
        extractions = []

        for sent in sentences:
            sent_text = sent["text"]
            sent_start = sent["start_char"]

            # Extract Dates
            for pattern in DATE_PATTERNS:
                for match in pattern.finditer(sent_text):
                    start = sent_start + match.start()
                    end = sent_start + match.end()
                    extractions.append(EntityMentionModel(
                        text=match.group(),
                        type="DATE",
                        start_char=start,
                        end_char=end,
                        confidence=self.confidence_threshold,
                        source_agents=["date_time"]
                    ))

            # Extract Times
            for pattern in TIME_PATTERNS:
                for match in pattern.finditer(sent_text):
                    start = sent_start + match.start()
                    end = sent_start + match.end()
                    extractions.append(EntityMentionModel(
                        text=match.group(),
                        type="TIME",
                        start_char=start,
                        end_char=end,
                        confidence=self.confidence_threshold,
                        source_agents=["date_time"]
                    ))

        return extractions
