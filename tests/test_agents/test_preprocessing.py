import pytest
from src.utils.text_cleaning import clean_text
from src.utils.tokenizer import segment_sentences
from src.models.pipeline_state import PipelineState
from src.agents.preprocessing_agent import PreprocessingAgent

def test_clean_text():
    raw_text = "Hello  World!   Let's check   spaces."
    cleaned = clean_text(raw_text)
    assert cleaned == "Hello World! Let's check spaces."

def test_segment_sentences():
    text = "Microsoft released Windows. Today is July 17th."
    sentences = segment_sentences(text)
    
    assert len(sentences) == 2
    assert sentences[0]["text"] == "Microsoft released Windows."
    assert sentences[0]["start_char"] == 0
    assert sentences[0]["end_char"] == 27
    
    assert sentences[1]["text"] == "Today is July 17th."
    assert sentences[1]["start_char"] == 28
    assert sentences[1]["end_char"] == 47

def test_preprocessing_agent():
    state = PipelineState(
        session_id="test-session",
        document_id="test-doc",
        text="Hello  World.  This is a test.",
        status="IN_PROGRESS"
    )
    agent = PreprocessingAgent(config={})
    updated_state = agent.process(state)
    
    assert updated_state.status == "IN_PROGRESS"
    assert updated_state.current_stage == "EXTRACTION"
    assert len(updated_state.sentences) == 2
    assert updated_state.sentences[0]["text"] == "Hello World."
