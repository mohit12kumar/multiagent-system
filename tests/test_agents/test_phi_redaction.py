import pytest
from unittest.mock import MagicMock
from src.models.pipeline_state import PipelineState
from src.agents.phi_redaction_agent import PHIRedactionAgent

def test_phi_redaction_regex_and_names():
    # 1. Setup mock MySQLStore
    mock_mysql = MagicMock()
    
    agent = PHIRedactionAgent(config={}, mysql_store=mock_mysql)
    
    # Text with Name, Date, and SSN
    text = "Patient Alice Smith (SSN: 000-12-3456) was seen on 07/17/2026."
    
    state = PipelineState(
        session_id="test-session",
        document_id="test-doc",
        text=text,
        status="IN_PROGRESS"
    )
    
    updated_state = agent.process(state)
    
    # Assert replacements occurred in text
    assert "[REDACTED_NAME]" in updated_state.text
    assert "[REDACTED_SSN]" in updated_state.text
    assert "[REDACTED_DATE]" in updated_state.text
    assert "Alice Smith" not in updated_state.text
    assert "000-12-3456" not in updated_state.text
    assert "07/17/2026" not in updated_state.text
    
    # Assert database logging helper was called 3 times
    assert mock_mysql.log_phi_redaction.call_count == 3
