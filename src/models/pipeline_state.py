from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from src.models.entity import EntityMentionModel


class PipelineState(BaseModel):
    session_id: str
    document_id: str
    text: str
    status: str = "PENDING"
    current_stage: str = "PREPROCESSING"
    error_message: Optional[str] = None

    # Text segmentation results
    sentences: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of sentence dicts containing text, start_char, and end_char"
    )

    # Extracted entity lists from different steps
    raw_extractions: Dict[str, List[EntityMentionModel]] = Field(
        default_factory=dict,
        description="Raw extractions grouped by agent name (e.g. 'spacy', 'hf')"
    )

    aggregated_entities: List[EntityMentionModel] = Field(
        default_factory=list,
        description="Entities after consensus and conflict resolution"
    )

    validated_entities: List[EntityMentionModel] = Field(
        default_factory=list,
        description="Entities after schema/taxonomy validations"
    )

    final_entities: List[EntityMentionModel] = Field(
        default_factory=list,
        description="Entities after vector matching / disambiguation"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict)
