import pytest
from src.models.pipeline_state import PipelineState
from src.models.entity import EntityMentionModel
from src.agents.aggregation_agent import AggregationAgent

def test_aggregation_span_resolution():
    state = PipelineState(
        session_id="test",
        document_id="doc",
        text="President Barack Obama visited the office."
    )
    
    # Simulating raw extractions
    # Agent 1 (SpaCy) extracts "Barack Obama" (PERSON)
    # Agent 2 (HuggingFace) extracts "President Barack Obama" (PER)
    state.raw_extractions = {
        "spacy": [
            EntityMentionModel(
                text="Barack Obama",
                type="PERSON",
                start_char=10,
                end_char=22,
                confidence=0.70,
                source_agents=["spacy"]
            )
        ],
        "hf": [
            EntityMentionModel(
                text="President Barack Obama",
                type="PER",
                start_char=0,
                end_char=22,
                confidence=0.85,
                source_agents=["hf"]
            )
        ]
    }
    
    agent = AggregationAgent(config={})
    updated_state = agent.process(state)
    
    # Overlap should resolve to a single entity
    assert len(updated_state.aggregated_entities) == 1
    
    merged = updated_state.aggregated_entities[0]
    # The winner is "President Barack Obama" (from HF due to higher confidence * weight)
    assert merged.text == "President Barack Obama"
    assert merged.type == "PER"
    assert merged.start_char == 0
    assert merged.end_char == 22
    # Combined sources should have both spacy and hf
    assert "spacy" in merged.source_agents
    assert "hf" in merged.source_agents
    # Boosted confidence score because two unique agents agreed
    assert merged.confidence > 0.85
