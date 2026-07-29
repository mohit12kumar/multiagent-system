import os
import json
import threading
from typing import Dict, Any, List, Optional
from src.monitoring.logger import logger

class KnowledgeLoader:
    """
    Lazy-loading, thread-safe, configuration-driven Clinical Knowledge Loader.
    Loads diseases, medications, labs, and guidelines dynamically from JSON configurations.
    No hardcoded disease or medication rules.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(KnowledgeLoader, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, base_dir: Optional[str] = None):
        if getattr(self, "_initialized", False):
            return

        if base_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            base_dir = os.path.join(project_root, "data", "knowledge_base")

        self.base_dir = base_dir
        self._diseases: Dict[str, Dict[str, Any]] = {}
        self._medications: Dict[str, Dict[str, Any]] = {}
        self._labs: Dict[str, Dict[str, Any]] = {}
        self._guidelines: Dict[str, Dict[str, Any]] = {}
        
        self._loaded = False
        self._initialized = True
        logger.info(f"KnowledgeLoader initialized with base_dir: {self.base_dir}")

    def _ensure_loaded(self):
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            self._load_all_configurations()
            self._loaded = True

    def _load_json_file(self, filename: str) -> List[Dict[str, Any]]:
        filepath = os.path.join(self.base_dir, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Knowledge file not found at {filepath}")
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    key = filename.replace(".json", "")
                    return data.get(key) or data.get("laboratories") or data.get("diseases") or data.get("medications") or data.get("guidelines") or []
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Failed to load JSON knowledge file {filepath}: {e}")
            return []

    def _load_all_configurations(self):
        # 1. Load Diseases
        disease_list = self._load_json_file("diseases.json")
        for dis in disease_list:
            name_key = dis.get("disease_name", "").strip().lower()
            if name_key:
                self._diseases[name_key] = dis
            icd10_key = dis.get("icd10", "").strip().lower()
            if icd10_key:
                self._diseases[icd10_key] = dis

        # 2. Load Medications
        med_list = self._load_json_file("medications.json")
        for med in med_list:
            gen_key = med.get("generic_name", "").strip().lower()
            if gen_key:
                self._medications[gen_key] = med
            rxn_key = med.get("rxnorm_code", "").strip()
            if rxn_key:
                self._medications[rxn_key] = med
            for brand in med.get("brand_names", []):
                self._medications[brand.strip().lower()] = med

        # 3. Load Labs
        lab_list = self._load_json_file("labs.json")
        for lab in lab_list:
            test_key = lab.get("test_name", "").strip().lower()
            canon_key = lab.get("canonical_name", "").strip().lower()
            loinc_key = lab.get("loinc_code", "").strip()
            if test_key:
                self._labs[test_key] = lab
            if canon_key:
                self._labs[canon_key] = lab
            if loinc_key:
                self._labs[loinc_key] = lab

        # 4. Load Guidelines
        gl_list = self._load_json_file("guidelines.json")
        for gl in gl_list:
            gl_id = gl.get("id", "").strip().lower()
            if gl_id:
                self._guidelines[gl_id] = gl

        logger.info(f"KnowledgeLoader successfully loaded {len(disease_list)} diseases, {len(med_list)} medications, {len(lab_list)} labs, {len(gl_list)} guidelines.")

    def get_disease(self, term: str) -> Optional[Dict[str, Any]]:
        self._ensure_loaded()
        if not term:
            return None
        t_low = term.strip().lower()
        return self._diseases.get(t_low)

    def get_medication(self, term: str) -> Optional[Dict[str, Any]]:
        self._ensure_loaded()
        if not term:
            return None
        t_low = term.strip().lower()
        return self._medications.get(t_low)

    def get_lab(self, term: str) -> Optional[Dict[str, Any]]:
        self._ensure_loaded()
        if not term:
            return None
        t_low = term.strip().lower()
        return self._labs.get(t_low)

    def get_all_diseases(self) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        unique = {}
        for d in self._diseases.values():
            unique[d.get("id", d.get("disease_name"))] = d
        return list(unique.values())

    def get_all_medications(self) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        unique = {}
        for m in self._medications.values():
            unique[m.get("id", m.get("generic_name"))] = m
        return list(unique.values())

    def get_all_labs(self) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        unique = {}
        for l in self._labs.values():
            unique[l.get("id", l.get("test_name"))] = l
        return list(unique.values())

    def get_all_guidelines(self) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        return list(self._guidelines.values())

    def register_disease_dynamically(self, disease_data: Dict[str, Any]):
        """Supports dynamically registering thousands of new diseases without restarting."""
        self._ensure_loaded()
        name_key = disease_data.get("disease_name", "").strip().lower()
        if name_key:
            with self._lock:
                self._diseases[name_key] = disease_data
                icd10_key = disease_data.get("icd10", "").strip().lower()
                if icd10_key:
                    self._diseases[icd10_key] = disease_data
            logger.info(f"Dynamically registered new disease concept: {disease_data.get('disease_name')}")
