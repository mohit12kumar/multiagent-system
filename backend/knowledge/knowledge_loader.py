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
        self._frequencies: Dict[str, Any] = {}
        self._routes: Dict[str, str] = {}
        self._timings: Dict[str, str] = {}
        self._dose_units: Dict[str, Any] = {}
        self._drug_aliases: Dict[str, Any] = {}
        self._drug_indications: Dict[str, str] = {}
        self._brand_generic: Dict[str, str] = {}
        
        self._loaded = False
        self._initialized = True

        # Knowledge Governance Controls
        self._approval_status: str = "APPROVED"  # DRAFT, APPROVED, DEPRECATED
        self._current_version: str = "v1.0.0"
        self._version_snapshots: Dict[str, Dict[str, Any]] = {}
        self._audit_log: List[Dict[str, Any]] = []

        logger.info(f"KnowledgeLoader initialized with base_dir: {self.base_dir}")

    def _ensure_loaded(self):
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            self._load_all_configurations()
            self._loaded = True

    def _load_json_file(self, filename: str) -> Any:
        filepath = os.path.join(self.base_dir, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Knowledge file not found at {filepath}")
            return {} if filename.endswith(".json") else []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    key = filename.replace(".json", "")
                    return data.get(key) or data.get("laboratories") or data.get("diseases") or data.get("medications") or data.get("guidelines") or data
                return data
        except Exception as e:
            logger.error(f"Failed to load JSON knowledge file {filepath}: {e}")
            return {}

    def _load_all_configurations(self):
        # 1. Load Diseases
        disease_list = self._load_json_file("diseases.json")
        if isinstance(disease_list, list):
            for dis in disease_list:
                name_key = dis.get("disease_name", "").strip().lower()
                if name_key:
                    self._diseases[name_key] = dis
                icd10_key = dis.get("icd10", "").strip().lower()
                if icd10_key:
                    self._diseases[icd10_key] = dis

        # 2. Load Medications
        med_list = self._load_json_file("medications.json")
        if isinstance(med_list, list):
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
        if isinstance(lab_list, list):
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
        if isinstance(gl_list, list):
            for gl in gl_list:
                gl_id = gl.get("id", "").strip().lower()
                if gl_id:
                    self._guidelines[gl_id] = gl

        # 5. Load Frequencies, Routes, Timings, Dose Units, Aliases, Indications
        freq_data = self._load_json_file("clinical_frequency.json")
        if isinstance(freq_data, dict):
            self._frequencies = freq_data.get("frequencies", freq_data)

        route_data = self._load_json_file("route_dictionary.json")
        if isinstance(route_data, dict):
            self._routes = route_data.get("routes", route_data)

        timing_data = self._load_json_file("timing_dictionary.json")
        if isinstance(timing_data, dict):
            self._timings = timing_data.get("timings", timing_data)

        dose_data = self._load_json_file("dose_units.json")
        if isinstance(dose_data, dict):
            self._dose_units = dose_data

        alias_data = self._load_json_file("drug_aliases.json")
        if isinstance(alias_data, dict):
            self._drug_aliases = alias_data.get("drug_aliases", alias_data)

        ind_data = self._load_json_file("drug_indications.json")
        if isinstance(ind_data, dict):
            self._drug_indications = ind_data.get("indications", ind_data)

        brand_data = self._load_json_file("brand_generic.json")
        if isinstance(brand_data, dict):
            self._brand_generic = brand_data.get("brand_to_generic", brand_data)

        logger.info(f"KnowledgeLoader successfully loaded diseases, medications, labs, guidelines, and enterprise clinical dictionaries.")

    def get_frequency_dict(self) -> Dict[str, Any]:
        self._ensure_loaded()
        return self._frequencies

    def get_route_dict(self) -> Dict[str, str]:
        self._ensure_loaded()
        return self._routes

    def get_timing_dict(self) -> Dict[str, str]:
        self._ensure_loaded()
        return self._timings

    def get_dose_units_dict(self) -> Dict[str, Any]:
        self._ensure_loaded()
        return self._dose_units

    def get_drug_aliases_dict(self) -> Dict[str, Any]:
        self._ensure_loaded()
        return self._drug_aliases

    def get_drug_indications_dict(self) -> Dict[str, str]:
        self._ensure_loaded()
        return self._drug_indications

    def get_brand_generic_dict(self) -> Dict[str, str]:
        self._ensure_loaded()
        return self._brand_generic

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

    # ── Knowledge Governance & Rollback Engine ────────────────────────────────

    def set_approval_status(self, status: str, approver: str = "System Admin"):
        """Sets approval status (DRAFT, APPROVED, DEPRECATED) with audit logging."""
        valid_statuses = {"DRAFT", "APPROVED", "DEPRECATED"}
        status_upper = status.upper()
        if status_upper not in valid_statuses:
            raise ValueError(f"Invalid status '{status}'. Must be one of {valid_statuses}")
        
        with self._lock:
            old_status = self._approval_status
            self._approval_status = status_upper
            self._audit_log.append({
                "action": "STATUS_CHANGE",
                "old_status": old_status,
                "new_status": status_upper,
                "actor": approver
            })
            logger.info(f"KnowledgeLoader approval status changed from {old_status} to {status_upper} by {approver}")

    def get_approval_status(self) -> str:
        return self._approval_status

    def create_version_snapshot(self, version_id: str, author: str = "System Admin") -> str:
        """Takes a snapshot of current knowledge dictionary states for instant rollback."""
        self._ensure_loaded()
        with self._lock:
            snapshot = {
                "version_id": version_id,
                "author": author,
                "diseases": dict(self._diseases),
                "medications": dict(self._medications),
                "labs": dict(self._labs),
                "guidelines": dict(self._guidelines),
                "status": self._approval_status
            }
            self._version_snapshots[version_id] = snapshot
            self._audit_log.append({
                "action": "CREATE_SNAPSHOT",
                "version_id": version_id,
                "author": author
            })
            logger.info(f"Created KnowledgeLoader version snapshot '{version_id}'")
            return version_id

    def rollback_to_version(self, version_id: str, actor: str = "System Admin") -> bool:
        """Rolls back knowledge state to a previously captured version snapshot."""
        with self._lock:
            if version_id not in self._version_snapshots:
                logger.error(f"Cannot rollback: Snapshot version '{version_id}' not found")
                return False
            
            snap = self._version_snapshots[version_id]
            self._diseases = dict(snap["diseases"])
            self._medications = dict(snap["medications"])
            self._labs = dict(snap["labs"])
            self._guidelines = dict(snap["guidelines"])
            self._approval_status = snap["status"]
            self._current_version = version_id

            self._audit_log.append({
                "action": "ROLLBACK",
                "target_version": version_id,
                "actor": actor
            })
            logger.info(f"Successfully rolled back KnowledgeLoader to version '{version_id}'")
            return True

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return list(self._audit_log)

