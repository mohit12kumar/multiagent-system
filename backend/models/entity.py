from pydantic import BaseModel, Field
from typing import List, Optional


class EntityMentionModel(BaseModel):
    id: Optional[str] = None
    text: str = Field(..., description="The exact text snippet of the entity")
    type: str = Field(..., description="The unified entity type (e.g., DISEASE, DRUG, SYMPTOM)")
    start_char: int = Field(..., description="Start character offset in the document")
    end_char: int = Field(..., description="End character offset in the document")
    confidence: float = Field(0.0, description="Extraction confidence score")
    source_agents: List[str] = Field(default_factory=list, description="Agents that extracted this entity")
    canonical_id: Optional[str] = Field(None, description="Linked canonical entity ID from database or taxonomy")
    canonical_name: Optional[str] = Field(None, description="Linked canonical entity name")
    cui: Optional[str] = Field(None, description="UMLS Concept Unique Identifier")
    icd10: Optional[str] = Field(None, description="ICD-10-CM code")
    needs_review: bool = Field(False, description="Flag indicating if mention requires physician review")
