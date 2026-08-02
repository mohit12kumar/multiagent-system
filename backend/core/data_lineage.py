"""
backend/core/data_lineage.py

Enterprise 11-Dimensional Data Lineage & Document Provenance Tracker.
Links extraction outcomes to explicit version vectors and checksum chains.
"""

import time
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ProvenanceVector:
    """
    11-Dimensional Asset Reproducibility Vector.
    """
    def __init__(
        self,
        pipeline_version: str = "v6.0.0",
        model_version: str = "med-gemini-3.6",
        prompt_version: str = "p_med_ner_v3.2",
        embedding_version: str = "text-embedding-3-large",
        knowledge_base_version: str = "kb_2026_q3",
        policy_version: str = "pol_hospital_v2",
        rule_dsl_version: str = "dsl_v1.4",
        fhir_schema_version: str = "FHIR_R4_v4.0.1",
        api_version: str = "v1.0",
        dataset_version: str = "clinical_eval_3500_v1",
        ontology_version: str = "SNOMED-CT_2026_LOINC_2.75_ICD10"
    ):
        self.pipeline_version = pipeline_version
        self.model_version = model_version
        self.prompt_version = prompt_version
        self.embedding_version = embedding_version
        self.knowledge_base_version = knowledge_base_version
        self.policy_version = policy_version
        self.rule_dsl_version = rule_dsl_version
        self.fhir_schema_version = fhir_schema_version
        self.api_version = api_version
        self.dataset_version = dataset_version
        self.ontology_version = ontology_version

    def to_dict(self) -> Dict[str, str]:
        return {
            "pipeline_version": self.pipeline_version,
            "model_version": self.model_version,
            "prompt_version": self.prompt_version,
            "embedding_version": self.embedding_version,
            "knowledge_base_version": self.knowledge_base_version,
            "policy_version": self.policy_version,
            "rule_dsl_version": self.rule_dsl_version,
            "fhir_schema_version": self.fhir_schema_version,
            "api_version": self.api_version,
            "dataset_version": self.dataset_version,
            "ontology_version": self.ontology_version,
        }


class FieldProvenance:
    """
    Tracks provenance of an individual extracted field down to character offsets and SHA-256 checksums.
    """
    def __init__(
        self,
        field_name: str,
        field_value: Any,
        doc_version: str,
        ocr_confidence: float,
        char_offsets: List[int],
        vector: Optional[ProvenanceVector] = None
    ):
        self.field_name = field_name
        self.field_value = field_value
        self.doc_version = doc_version
        self.ocr_confidence = ocr_confidence
        self.char_offsets = char_offsets
        self.vector = vector or ProvenanceVector()
        self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        payload = f"{self.field_name}:{self.field_value}:{self.doc_version}:{self.char_offsets}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "field_value": self.field_value,
            "sha256_checksum": self.checksum,
            "doc_version": self.doc_version,
            "ocr_confidence": self.ocr_confidence,
            "char_offsets": self.char_offsets,
            "provenance_vectors": self.vector.to_dict(),
        }


class DataLineageTracker:
    """
    Enterprise Data Lineage & Provenance Governance Manager.
    """
    def __init__(self, document_id: str, doc_version: str = "v1.0"):
        self.document_id = document_id
        self.doc_version = doc_version
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.provenance_vector = ProvenanceVector()
        self.field_records: Dict[str, FieldProvenance] = {}

    def set_provenance_vector(self, vector: ProvenanceVector):
        """Overrides default 11-dimensional reproducibility vector."""
        self.provenance_vector = vector

    def add_field_provenance(
        self,
        field_name: str,
        field_value: Any,
        ocr_confidence: float = 1.0,
        char_offsets: Optional[List[int]] = None
    ) -> FieldProvenance:
        """Records provenance for a specific extracted entity/field."""
        char_offsets = char_offsets or [0, 0]
        prov = FieldProvenance(
            field_name=field_name,
            field_value=field_value,
            doc_version=self.doc_version,
            ocr_confidence=ocr_confidence,
            char_offsets=char_offsets,
            vector=self.provenance_vector
        )
        self.field_records[field_name] = prov
        return prov

    def export_lineage_report(self) -> Dict[str, Any]:
        """Generates the full 11-Dimensional Data Lineage & Provenance Report."""
        return {
            "document_id": self.document_id,
            "doc_version": self.doc_version,
            "timestamp": self.created_at,
            "11_dimensional_vectors": self.provenance_vector.to_dict(),
            "field_provenance_chain": [prov.to_dict() for prov in self.field_records.values()]
        }


class DataLineageEngine:
    """
    Constructs 11-dimensional audit provenance lineage records (backwards compatibility).
    """

    DEFAULT_PROVENANCE_VECTORS = ProvenanceVector().to_dict()

    @classmethod
    def attach_provenance(
        cls,
        field_value: Any,
        raw_text: str,
        start_char: int,
        end_char: int,
        agent_name: str,
        ocr_confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Builds 11-dimensional lineage provenance dictionary.
        """
        doc_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        snippet = raw_text[max(0, start_char):min(len(raw_text), end_char)]

        provenance = {
            "field_value": field_value,
            "evidence_snippet": snippet,
            "document_sha256": doc_hash,
            "start_char": start_char,
            "end_char": end_char,
            "extracting_agent": agent_name,
            "ocr_confidence": ocr_confidence or 1.0,
            "timestamp": time.time(),
            "lineage_vectors": dict(cls.DEFAULT_PROVENANCE_VECTORS)
        }
        return provenance
