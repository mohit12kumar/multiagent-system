import pytest
from unittest.mock import MagicMock
from src.models.pipeline_state import PipelineState
from src.models.entity import EntityMentionModel
from src.agents.disambiguation_agent import DisambiguationAgent
from src.db.models import CanonicalEntity

def test_disambiguation_linking():
    # 1. Setup mock ChromaStore
    mock_chroma = MagicMock()
    mock_chroma.query_similar_entities.return_value = [
        {"id": "c1", "name": "Google", "type": "ORGANIZATION", "similarity": 0.95}
    ]
    
    # 2. Setup mock MySQLStore
    mock_mysql = MagicMock()
    mock_entity = CanonicalEntity(id="c1", name="Google", type="ORGANIZATION", description="Search Engine")
    mock_mysql.get_canonical_entity_by_id.return_value = mock_entity
    
    # Initialize agent
    agent = DisambiguationAgent(
        config={"similarity_threshold": 0.80},
        chroma_store=mock_chroma,
        mysql_store=mock_mysql
    )
    
    # Pipeline State
    state = PipelineState(
        session_id="test",
        document_id="doc",
        text="Google is hiring."
    )
    state.validated_entities = [
        EntityMentionModel(
            text="Google",
            type="ORGANIZATION",
            start_char=0,
            end_char=6,
            confidence=0.80,
            source_agents=["spacy"]
        )
    ]
    
    updated_state = agent.process(state)
    
    # Entity should be linked to c1
    linked_entity = updated_state.final_entities[0]
    assert linked_entity.canonical_id == "c1"
    assert linked_entity.canonical_name == "Google"
    # Linked items with high confidence do not need review
    assert linked_entity.needs_review is False
