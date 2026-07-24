import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.connection import Base
from backend.orchestrator.coordinator import Coordinator
from backend.agents.phi_redaction_agent import PHIRedactionAgent

@pytest.fixture(scope="module")
def db_session():
    # Use isolated in-memory SQLite for test execution
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()

def test_phi_redaction_agent():
    agent = PHIRedactionAgent()
    from backend.models.pipeline_state import PipelineState
    state = PipelineState(
        session_id="test_sess_1",
        document_id="test_doc_1",
        text="Patient Mr. John Doe (DOB: 05/12/1980) presents with headache."
    )
    result = agent.process(state)
    assert "[REDACTED NAME]" in result.text or "Mr. [REDACTED NAME]" in result.text or "[REDACTED DOB]" in result.text

def test_full_coordinator_pipeline(db_session):
    coordinator = Coordinator(db_session)
    clinical_note = "Patient presents with severe headache and dizziness. Diagnosed with Hypertension. Prescribed Amlodipine 5 mg once daily for 30 days."
    output = coordinator.run_pipeline(clinical_note)
    
    assert "patient_summary" in output
    assert len(output["patient_summary"]) > 0
    summary = output["patient_summary"][0]
    assert summary["disease"] == "Hypertension"
    assert any(s.lower() in ["headache", "dizziness"] for s in summary["symptoms"])
    assert summary["medication"] is not None
    assert summary["medication"]["name"].lower() == "amlodipine"
