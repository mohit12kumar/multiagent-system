import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.connection import Base
from src.orchestrator.coordinator import Coordinator
from src.db.models import PipelineSession, EntityMention, ReviewQueue, PHIAuditLog, Document

# Set environment to test to enforce SQLite configuration
os.environ["ENV"] = "test"

@pytest.fixture
def db_session():
    """Sets up an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_pipeline_e2e_medical(db_session):
    # Initialize coordinator with the in-memory DB session
    coordinator = Coordinator(db_session)
    
    # Override active extractors to only run regex-based dosage_frequency to bypass model downloads
    coordinator.router.active_extractors = ["dosage_frequency"]
    
    # Input note containing PHI name, date, and dosage info
    clinical_note = "Patient Alice Smith was seen on 07/17/2026. Prescribed Lisinopril 10mg once daily."
    
    output = coordinator.run_pipeline(clinical_note, {"source": "e2e_medical_test"})
    
    # 1. Verify pipeline structured output
    assert output["status"] == "COMPLETED"
    assert "session_id" in output
    assert len(output["entities"]) == 2
    
    # Assert extracted entities
    entities = output["entities"]
    types = [e["type"] for e in entities]
    texts = [e["text"] for e in entities]
    
    assert "DOSAGE" in types
    assert "FREQUENCY" in types
    assert "10mg" in texts
    assert "once daily" in texts
    
    # 2. Verify PHI Redaction in database
    session_id = output["session_id"]
    db_session.expire_all()
    
    # Check that stored document text is REDACTED
    doc_record = db_session.query(Document).filter(Document.id == output["document_id"]).first()
    assert doc_record is not None
    assert "Alice Smith" not in doc_record.content
    assert "07/17/2026" not in doc_record.content
    assert "[REDACTED_NAME]" in doc_record.content
    assert "[REDACTED_DATE]" in doc_record.content
    
    # Check that phi_audit_log is populated
    audits = db_session.query(PHIAuditLog).filter(PHIAuditLog.session_id == session_id).all()
    assert len(audits) == 2
    
    audit_types = [a.field_type for a in audits]
    assert "NAME" in audit_types
    assert "DATE" in audit_types
    
    # Verify entity mentions are mapped
    mentions = db_session.query(EntityMention).filter(EntityMention.session_id == session_id).all()
    assert len(mentions) == 2
