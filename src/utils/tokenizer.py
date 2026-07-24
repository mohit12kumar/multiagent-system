import re
from typing import Any, Dict, List

# A simple regex sentence splitter that detects boundaries like periods, question marks, and exclamation marks,
# followed by spacing and capitalization, while avoiding common abbreviations (e.g., Mr., Dr., etc.)
SENTENCE_SPLIT_REGEX = re.compile(
    r'(?<!\bMr)(?<!\bMs)(?<!\bDr)(?<!\bProf)(?<!\bSr)(?<!\bJr)(?<!\bCo)(?<!\bInc)(?<!\bLtd)(?<!\bvs)\.[ \t\n]+(?=[A-Z0-9]|\b)|[.!?]\n+'
)


def segment_sentences(text: str) -> List[Dict[str, Any]]:
    """
    Splits the text into sentences, tracking character start and end offsets.
    Uses regex fallback to ensure compatibility when SpaCy is loading or unavailable.
    """
    if not text:
        return []

    sentences = []

    # We find sentence boundaries using regex
    last_end = 0
    for match in SENTENCE_SPLIT_REGEX.finditer(text):
        end = match.end()
        sentence_text = text[last_end:end].strip()
        if sentence_text:
            sentences.append({
                "text": sentence_text,
                "start_char": last_end,
                "end_char": last_end + len(sentence_text)
            })
        last_end = end

    # Append the last chunk of text if any remains
    remaining_text = text[last_end:].strip()
    if remaining_text:
        sentences.append({
            "text": remaining_text,
            "start_char": last_end,
            "end_char": last_end + len(remaining_text)
        })

    return sentences
