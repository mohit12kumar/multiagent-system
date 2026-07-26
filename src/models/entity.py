from pydantic import BaseModel, Field
from typing import List, Optional


class EntityMentionModel(BaseModel):
    id: Optional[str] = None
    text: str = Field(..., description="The exact text snippet of the entity")
    type: str = Field(...,
                      description="The unified entity type (e.g., PERSON, ORGANIZATION)")
    start_char: int = Field(...,
                            description="Start character offset in the document")
    end_char: int = Field(...,
                          description="End character offset in the document")
    confidence: float = Field(0.0, description="Extraction confidence score")
    source_agents: List[str] = Field(
        default_factory=list, description="Agents that extracted this entity")
    canonical_id: Optional[str] = Field(
        None, description="Linked canonical entity ID from MySQL")
    canonical_name: Optional[str] = Field(
        None, description="Linked canonical entity name")
    needs_review: bool = Field(
        False, description="Flag indicating this mention requires human review")
