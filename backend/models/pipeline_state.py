from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from backend.models.entity import EntityMentionModel


class PipelineState(BaseModel):
    session_id: str
    document_id: str
    user_id: Optional[str] = None
    text: str
    original_text: Optional[str] = None
    status: str = "PENDING"
    current_stage: str = "PREPROCESSING"
    error_message: Optional[str] = None
    failed_stages: List[str] = Field(default_factory=list, description="List of stage names that encountered errors")

    # Text segmentation & POS NLP outputs
    sentences: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of sentence dicts containing text, start_char, and end_char"
    )
    pos_tags: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="POS tags generated during linguistic processing"
    )

    # HIPAA PHI Redaction Audits
    phi_redactions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Audit entries for redacted sensitive PHI elements"
    )

    # Entity Extraction & Processing Stages
    raw_extractions: Dict[str, List[EntityMentionModel]] = Field(
        default_factory=dict,
        description="Raw entity extractions grouped by agent name"
    )
    aggregated_entities: List[EntityMentionModel] = Field(
        default_factory=list,
        description="Consolidated entity mentions after voting & overlap resolution"
    )
    validated_entities: List[EntityMentionModel] = Field(
        default_factory=list,
        description="Entities validated against taxonomy rules & medical consistency"
    )
    final_entities: List[EntityMentionModel] = Field(
        default_factory=list,
        description="Final normalized entity mentions after CUI/vector matching"
    )

    # Clinical Relations & Summaries
    disease_relations: List[Any] = Field(
        default_factory=list,
        description="Structured disease-to-symptom-to-drug indication mappings"
    )
    medication_relations: List[Any] = Field(
        default_factory=list,
        description="Medication details including dosage, frequency, route, and duration"
    )
    patient_summary: List[Any] = Field(
        default_factory=list,
        description="Summary condition cards for clinical view"
    )

    # Document & Session Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
