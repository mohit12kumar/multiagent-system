import json
import os
import difflib
from typing import Dict, Any, List


class MedicalSpellCorrectionAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.cutoff = self.config.get("spell_cutoff", 0.82)
        self.vocab = []
        
        # Load vocabulary from clinical_vocab.json relative to repository config directory
        default_vocab_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "config", "clinical_vocab.json"
        )
        vocab_path = os.getenv("CLINICAL_VOCAB_PATH", default_vocab_path)
        if os.path.exists(vocab_path):
            try:
                with open(vocab_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Aggregate all terms
                    for category in ["diseases", "symptoms", "drugs", "lab_markers"]:
                        if category in data:
                            self.vocab.extend([item.lower() for item in data[category]])
                # Deduplicate
                self.vocab = list(set(self.vocab))
            except Exception as e:
                print(f"[SpellCorrectionAgent] WARNING: Failed loading vocab from {vocab_path}: {e}")
        else:
            print(f"[SpellCorrectionAgent] WARNING: Vocabulary file not found at '{vocab_path}'. Spell correction will be limited.")

    def correct_word(self, word: str) -> str:
        """Suggests the closest matching vocabulary term if spelling similarity is high."""
        if not word or len(word) < 4:
            return word
            
        w_low = word.lower()
        if w_low in self.vocab:
            return word

        matches = difflib.get_close_matches(w_low, self.vocab, n=1, cutoff=self.cutoff)
        if matches:
            # Preserve case styling if matching original
            matched = matches[0]
            if word[0].isupper() and len(word) > 1:
                return matched.capitalize()
            return matched
        return word

    def correct_phrase(self, phrase: str) -> str:
        """Normalizes each word in a clinical search phrase."""
        if not phrase:
            return ""
        words = phrase.split()
        corrected = [self.correct_word(w) for w in words]
        return " ".join(corrected)
