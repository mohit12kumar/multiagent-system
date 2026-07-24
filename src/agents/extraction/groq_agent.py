import os
import json
import requests
from typing import List
from src.models.entity import EntityMentionModel
from src.monitoring.logger import logger


class GroqAgent:
    def __init__(self, config: dict):
        self.config = config or {}
        self.model_name = self.config.get(
            "model_name", "llama-3.3-70b-specdec")
        self.confidence_threshold = self.config.get(
            "confidence_threshold", 0.75)
        self.supported_entities = self.config.get(
            "supported_entities", ["DISEASE", "DRUG", "DOSAGE", "FREQUENCY", "ANATOMY"])
        self.system_prompt = self.config.get("system_prompt", "")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.max_llm_calls = self.config.get("max_llm_calls_per_document", 5)

    def extract(self, sentences: List[dict]) -> List[EntityMentionModel]:
        """
        Extracts medical entities using the Groq API.
        """
        extractions = []

        if not self.api_key:
            logger.error(
                "Groq API key not found. Please set GROQ_API_KEY in your environment or .env file.")
            return extractions

        # Enforce max LLM call constraints
        if len(sentences) > self.max_llm_calls:
            logger.warning(
                f"Groq execution capped to first {self.max_llm_calls} sentences of {len(sentences)}.")
            sentences = sentences[:self.max_llm_calls]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        for sent in sentences:
            sent_text = sent["text"]
            sent_start = sent["start_char"]

            prompt = f"Extract clinical entities of types {', '.join(self.supported_entities)} from this sentence.\n\nSentence: \"{sent_text}\""

            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"}
            }

            try:
                response = requests.post(
                    self.api_url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()

                resp_json = response.json()
                content = resp_json.get("choices", [{}])[0].get(
                    "message", {}).get("content", "")
                if not content:
                    continue

                parsed_json = json.loads(content)
                raw_entities = []
                if isinstance(parsed_json, list):
                    raw_entities = parsed_json
                elif isinstance(parsed_json, dict):
                    for key in ["entities", "results", "values", "data"]:
                        if key in parsed_json and isinstance(parsed_json[key], list):
                            raw_entities = parsed_json[key]
                            break
                    if not raw_entities:
                        # Fallback for dict containing arrays of terms or raw key-value entities
                        for k, v in parsed_json.items():
                            if isinstance(v, list):
                                for item in v:
                                    if isinstance(item, str):
                                        raw_entities.append(
                                            {"text": item, "type": k})
                                    elif isinstance(item, dict):
                                        raw_entities.append(item)
                            elif isinstance(v, str):
                                raw_entities.append({"text": v, "type": k})

                for raw in raw_entities:
                    if not isinstance(raw, dict):
                        continue

                    text = raw.get("text") or raw.get(
                        "entity") or raw.get("name")
                    ent_type = raw.get("type") or raw.get(
                        "category") or raw.get("label")
                    confidence = float(
                        raw.get("confidence", self.confidence_threshold))

                    if not text or not ent_type:
                        continue

                    ent_type = ent_type.upper().strip()
                    if ent_type not in [t.upper() for t in self.supported_entities]:
                        continue

                    start_idx = sent_text.find(text)
                    if start_idx == -1:
                        start_idx = sent_text.lower().find(text.lower())
                        if start_idx != -1:
                            text = sent_text[start_idx:start_idx + len(text)]

                    if start_idx != -1:
                        start_char = sent_start + start_idx
                        end_char = start_char + len(text)

                        extractions.append(EntityMentionModel(
                            text=text,
                            type=ent_type,
                            start_char=start_char,
                            end_char=end_char,
                            confidence=confidence,
                            source_agents=["groq"]
                        ))
            except Exception as e:
                logger.warning(f"Groq query failed: {e}")

        return extractions
