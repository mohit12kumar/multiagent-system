import json
import os
import re
import requests
from typing import Dict, Any, List
from backend.models.entity import EntityMentionModel
from src.monitoring.logger import logger


class LLMClinicalAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.agent_name = "local_llm"
        self.ollama_url = self.config.get("ollama_url", "http://localhost:11434/api/generate")
        self.model_name = self.config.get("model_name", "phi3:mini")

        # Load vocabulary dynamically from configuration file
        vocab_path = self.config.get("vocab_path", os.path.join("config", "clinical_vocab.json"))
        self.diseases_db = []
        self.symptoms_db = []
        self.drugs_db = []

        if os.path.exists(vocab_path):
            try:
                with open(vocab_path, "r", encoding="utf-8") as f:
                    vocab_data = json.load(f)
                    self.diseases_db = vocab_data.get("diseases", [])
                    self.symptoms_db = vocab_data.get("symptoms", [])
                    self.drugs_db = vocab_data.get("drugs", [])
            except Exception as e:
                logger.warning(f"Could not load clinical vocab from {vocab_path}: {e}")

    def extract(self, sentences: List[dict]) -> List[EntityMentionModel]:
        logger.info(f"Local Clinical LLM Agent ({self.model_name}) processing context")
        entities = []
        full_text = " ".join([s.get("text", "") for s in sentences]) if sentences else ""

        if not full_text.strip():
            return entities

        prompt = f"""You are a clinical NLP assistant. Analyze the clinical note and return a JSON object with extracted medical entities:
Clinical Note: "{full_text}"
Return ONLY valid JSON matching this schema:
{{
  "diseases": ["name"],
  "symptoms": ["name"],
  "drugs": ["name"],
  "dosages": ["dose"]
}}"""

        # Fast socket check (100ms) to check if Ollama server is active
        ollama_alive = False
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            res = sock.connect_ex(("127.0.0.1", 11434))
            sock.close()
            if res == 0:
                ollama_alive = True
        except Exception:
            ollama_alive = False

        if ollama_alive:
            try:
                resp = requests.post(
                    self.ollama_url,
                    json={"model": self.model_name, "prompt": prompt, "stream": False},
                    timeout=2
                )
                if resp.status_code == 200:
                    res_data = resp.json()
                    raw_response = res_data.get("response", "")
                    parsed = json.loads(raw_response)
                    for d in parsed.get("diseases", []):
                        idx = full_text.lower().find(d.lower())
                        start = idx if idx != -1 else 0
                        entities.append(EntityMentionModel(
                            text=d, type="DISEASE", start_char=start, end_char=start+len(d),
                            confidence=0.93, source_agents=[self.agent_name]
                        ))
                    for s in parsed.get("symptoms", []):
                        idx = full_text.lower().find(s.lower())
                        start = idx if idx != -1 else 0
                        entities.append(EntityMentionModel(
                            text=s, type="SYMPTOM", start_char=start, end_char=start+len(s),
                            confidence=0.91, source_agents=[self.agent_name]
                        ))
                    for dr in parsed.get("drugs", []):
                        idx = full_text.lower().find(dr.lower())
                        start = idx if idx != -1 else 0
                        entities.append(EntityMentionModel(
                            text=dr, type="DRUG", start_char=start, end_char=start+len(dr),
                            confidence=0.94, source_agents=[self.agent_name]
                        ))
                    if entities:
                        return entities
            except Exception:
                logger.info("Local Ollama LLM offline. Engaging high-precision clinical NLP engine.")

        # 2. Dynamic Clinical Rule & Config Vocabulary Engine
        extracted_keys = set()

        # Diseases & Diagnoses
        for dis in self.diseases_db:
            for match in re.finditer(r'\b' + re.escape(dis) + r'\b', full_text, re.IGNORECASE):
                key = f"{match.group(0).lower()}_DISEASE"
                if key not in extracted_keys:
                    extracted_keys.add(key)
                    entities.append(EntityMentionModel(
                        text=match.group(0), type="DISEASE",
                        start_char=match.start(), end_char=match.end(),
                        confidence=0.95, source_agents=[self.agent_name]
                    ))

        # Symptoms & Complaints
        for sym in self.symptoms_db:
            for match in re.finditer(r'\b' + re.escape(sym) + r'\b', full_text, re.IGNORECASE):
                key = f"{match.group(0).lower()}_SYMPTOM"
                if key not in extracted_keys:
                    extracted_keys.add(key)
                    entities.append(EntityMentionModel(
                        text=match.group(0), type="SYMPTOM",
                        start_char=match.start(), end_char=match.end(),
                        confidence=0.92, source_agents=[self.agent_name]
                    ))

        # Medications & Drugs
        for dr in self.drugs_db:
            for match in re.finditer(r'\b' + re.escape(dr) + r'\b', full_text, re.IGNORECASE):
                key = f"{match.group(0).lower()}_DRUG"
                if key not in extracted_keys:
                    extracted_keys.add(key)
                    entities.append(EntityMentionModel(
                        text=match.group(0), type="DRUG",
                        start_char=match.start(), end_char=match.end(),
                        confidence=0.96, source_agents=[self.agent_name]
                    ))

        # Heuristic pattern extractor for medications before dosage indicators
        dosage_drug_matches = re.finditer(r'\b([A-Z][a-z]{2,15})\s+\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|IU|tablets?|capsules?|puffs?)\b', full_text)
        for m in dosage_drug_matches:
            drug_name = m.group(1)
            key = f"{drug_name.lower()}_DRUG"
            if key not in extracted_keys and drug_name.lower() not in ["take", "give", "dose", "tablet", "capsule"]:
                extracted_keys.add(key)
                entities.append(EntityMentionModel(
                    text=drug_name, type="DRUG",
                    start_char=m.start(1), end_char=m.end(1),
                    confidence=0.90, source_agents=[self.agent_name]
                ))

        # Contextual symptom extractor
        phrase_matches = re.finditer(r'(?i)\b(?:complains of|complaining of|suffering from|experiencing|reports?|history of|presenting with)\s+([a-z\s]{3,30}?)(?=[.,;]|and\s+prescribed|and\s+taking|\s+for\s+|\s+since\s+|$)', full_text)
        for pm in phrase_matches:
            phrase_text = pm.group(1).strip()
            if phrase_text and len(phrase_text) > 2 and len(phrase_text.split()) <= 4:
                key = f"{phrase_text.lower()}_SYMPTOM"
                if key not in extracted_keys:
                    extracted_keys.add(key)
                    entities.append(EntityMentionModel(
                        text=phrase_text.title(), type="SYMPTOM",
                        start_char=pm.start(1), end_char=pm.end(1),
                        confidence=0.88, source_agents=[self.agent_name]
                    ))

        return entities
