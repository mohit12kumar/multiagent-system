import pytest
from unittest.mock import MagicMock
from src.agents.extraction.date_time_agent import DateTimeAgent
from src.agents.extraction.spacy_agent import SpacyAgent
from src.agents.extraction.hf_agent import HfAgent

def test_date_time_agent():
    sentences = [
        {"text": "We met on 2026-07-17 at 11:25 AM.", "start_char": 0, "end_char": 33}
    ]
    agent = DateTimeAgent(config={})
    extractions = agent.extract(sentences)
    
    # Expecting 2 extractions: one date, one time
    assert len(extractions) == 2
    
    dates = [e for e in extractions if e.type == "DATE"]
    times = [e for e in extractions if e.type == "TIME"]
    
    assert len(dates) == 1
    assert dates[0].text == "2026-07-17"
    assert dates[0].start_char == 10
    assert dates[0].end_char == 20
    
    assert len(times) == 1
    assert times[0].text == "11:25 AM"
    assert times[0].start_char == 24
    assert times[0].end_char == 32

def test_spacy_agent_mock():
    # Mock spacy nlp model
    mock_nlp = MagicMock()
    mock_ent = MagicMock()
    mock_ent.text = "Google"
    mock_ent.label_ = "ORG"
    mock_ent.start_char = 0
    mock_ent.end_char = 6
    
    mock_doc = MagicMock()
    mock_doc.ents = [mock_ent]
    mock_nlp.return_value = mock_doc
    
    agent = SpacyAgent(config={"model_name": "mock"})
    agent.nlp = mock_nlp
    
    sentences = [{"text": "Google released a model.", "start_char": 10, "end_char": 34}]
    extractions = agent.extract(sentences)
    
    assert len(extractions) == 1
    assert extractions[0].text == "Google"
    assert extractions[0].type == "ORG"
    assert extractions[0].start_char == 10
    assert extractions[0].end_char == 16

def test_hf_agent_mock():
    # Mock Hugging Face pipeline
    mock_pipe = MagicMock()
    mock_pipe.return_value = [
        {"word": "Elon Musk", "entity_group": "PER", "score": 0.98, "start": 0, "end": 9}
    ]
    
    agent = HfAgent(config={})
    agent.pipeline = mock_pipe
    agent._initialized = True
    
    sentences = [{"text": "Elon Musk is CEO.", "start_char": 5, "end_char": 22}]
    extractions = agent.extract(sentences)
    
    assert len(extractions) == 1
    assert extractions[0].text == "Elon Musk"
    assert extractions[0].type == "PER"
    assert extractions[0].start_char == 5
    assert extractions[0].end_char == 14
