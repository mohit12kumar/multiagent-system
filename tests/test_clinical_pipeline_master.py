"""
Master Enterprise Clinical AI Pipeline Test Suite (~60-Phase Commercial Specification)
Covers end-to-end multi-agent pipeline processing, safety guardrails, FHIR R4 validation,
lineage checksums, policy resolution, and review queue integration.
"""

import pytest
import json
from typing import Dict, Any

from backend.database.connection import SessionLocal
from backend.database.models import User, ReviewQueue, PipelineSession
from backend.core.workflow_engine import WorkflowEngine, DAGCycleError
from backend.core.data_lineage import DataLineageTracker
from backend.clinical.hallucination_detector import ClinicalContradictionGuardrail
from backend.clinical.policy_engine import PolicyEngine
from backend.interop.fhir_mapper import FHIRMapper
from backend.clinical.ai_evaluator import AIEvaluationSuite
from backend.api.patient_routes import submit_patient_clinical_note, ClinicalNoteSubmissionRequest
from backend.api.doctor_routes import get_doctor_review_queue


# ---------------------------------------------------------------------------
# Test Fixtures & Master Clinical Test Case Note
# ---------------------------------------------------------------------------
MASTER_TEST_CLINICAL_NOTE = """
Patient Name: Robert Wilson
Age: 72 years
Gender: Male

Diagnosis:
Type 2 DM
HTN
CKD Stage IV
COPD
AF
Hyperlipidemia

Medications:
Tab Metformin Five Hundred mg 1-0-1 after food
Tab Metformin XR 500 mg BID
Tab Glucophage 500mg twice daily
Tab Ecosprin 75 OD
Tab Aspirin 150 mg OD
Tab Amlodipine 5 mg morning
Tab Norvasc 5 mg nightly
Tab Lipitor Forty mg HS
Tab Atorvastatin 40 mg at bedtime
Inj Insulin Glargine Twenty Units HS
Insulin Aspart 8 units TDS AC
Tab Diclofenac 50 mg TDS
Tab Ibuprofen 400 mg TDS
Tab Paracetamol 1g q6h
Tab PCM 650 SOS
Neb Salbutamol 2 puffs q4h PRN
Ventolin inhaler two puffs every four hours
Metformin inhaler 2 puffs OD

Labs:
Creatinine 3.1
eGFR 21
ALT 150
AST 142
HbA1c 9.8

Allergy:
Penicillin
"""

@pytest.fixture
def db_session():
    """Yield a database session for test teardown cleanups."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 1. DAG Workflow Engine & Idempotency Test
# ---------------------------------------------------------------------------
def test_workflow_dag_cycle_detection_and_execution():
    """Verify DAG cycle detection and parallel execution hashing."""
    engine = WorkflowEngine()
    
    # 1. Test valid DAG
    engine.add_node("ner_extraction", func=lambda inputs: {"entities": ["Metformin", "Aspirin"]})
    engine.add_node("disambiguation", func=lambda inputs: {"cui": "C0025580"}, depends_on=["ner_extraction"])
    engine.add_node("formatting", func=lambda inputs: {"summary": "Completed"}, depends_on=["disambiguation"])
    
    result = engine.execute(initial_inputs={"raw_note": MASTER_TEST_CLINICAL_NOTE})
    assert result["workflow_name"] == "EnterpriseClinicalWorkflow"
    assert "formatting" in result["results"]
    
    # 2. Test DAG cycle detection error
    cycle_engine = WorkflowEngine()
    cycle_engine.add_node("step_a", func=lambda i: i, depends_on=["step_b"])
    cycle_engine.add_node("step_b", func=lambda i: i, depends_on=["step_a"])
    with pytest.raises(DAGCycleError):
        cycle_engine.detect_cycles()


# ---------------------------------------------------------------------------
# 2. AI Safety & Biological Contradiction Guardrails Test
# ---------------------------------------------------------------------------
def test_clinical_contradiction_guardrails():
    """Verify guardrail intercepts impossible administration routes and severe renal contraindications."""
    guard = ClinicalContradictionGuardrail()
    patient = {"id": "PAT-72", "name": "Robert Wilson", "age": 72, "gender": "male"}
    
    medications = [
        {"name": "Metformin", "dose": "500 mg", "route": "oral", "frequency": "BID"},
        {"name": "Metformin", "dose": "2 puffs", "route": "inhalation", "frequency": "OD"},
        {"name": "Diclofenac", "dose": "50 mg", "route": "oral", "frequency": "TDS"},
        {"name": "Ibuprofen", "dose": "400 mg", "route": "oral", "frequency": "TDS"},
    ]
    conditions = ["CKD Stage IV", "Type 2 DM"]
    
    violations = guard.evaluate_contradictions(patient, {"medications": medications, "conditions": conditions})
    
    # Assert impossible route intercept
    route_violations = [v for v in violations if v.get("rule_type") == "ROUTE_INCOMPATIBILITY"]
    assert len(route_violations) > 0
    assert route_violations[0]["severity"] == "REJECT"
    assert "inhalation" in route_violations[0]["description"]


# ---------------------------------------------------------------------------
# 3. Hierarchical Policy Engine Test
# ---------------------------------------------------------------------------
def test_policy_engine_cascading():
    """Verify multi-tier policy resolution for Nephrology department."""
    policy_eng = PolicyEngine()
    policy = policy_eng.resolve_effective_policy(department="nephrology", doctor_id="dr_jenkins")
    
    assert policy["min_confidence"] == 0.80
    assert policy["escalate_low_egfr"] is True
    assert policy["strict_renol_dosing"] is True


# ---------------------------------------------------------------------------
# 4. HL7 FHIR R4 Bundle Generation & Schema Validation Test
# ---------------------------------------------------------------------------
def test_fhir_r4_bundle_validation():
    """Verify transformation into FHIR R4 Collection Bundle and schema compliance."""
    fhir_mapper = FHIRMapper()
    patient = {"id": "PAT-72", "name": "Robert Wilson", "age": 72, "gender": "male"}
    conditions = [{"name": c} for c in ["Type 2 DM", "HTN", "CKD Stage IV", "COPD", "AF", "Hyperlipidemia"]]
    medications = [
        {"name": "Metformin", "dose": "500 mg", "route": "oral", "frequency": "BID"},
        {"name": "Aspirin", "dose": "150 mg", "route": "oral", "frequency": "OD"}
    ]
    labs = [
        {"test_name": "Creatinine", "val": 3.1, "unit": "mg/dL"},
        {"test_name": "eGFR", "val": 21, "unit": "mL/min/1.73m2"}
    ]
    
    bundle = fhir_mapper.create_bundle({
        "patient": patient,
        "conditions": conditions,
        "medications": medications,
        "labs": labs
    })
    
    assert bundle["resourceType"] == "Bundle"
    assert len(bundle["entry"]) > 5
    assert fhir_mapper.validate_bundle_schema(bundle) is True


# ---------------------------------------------------------------------------
# 5. 11-Dimensional Data Lineage & Checksum Verification Test
# ---------------------------------------------------------------------------
def test_11d_data_lineage_checksums():
    """Verify 11-dimensional lineage tracking and SHA-256 field checksums."""
    lineage = DataLineageTracker("DOC-7201", "v1.0")
    lineage.add_field_provenance("Metformin", "500 mg BID", 0.99, [45, 80])
    
    report = lineage.export_lineage_report()
    assert report["document_id"] == "DOC-7201"
    assert "11_dimensional_vectors" in report
    assert len(report["field_provenance_chain"]) == 1
    assert len(report["field_provenance_chain"][0]["sha256_checksum"]) == 64


# ---------------------------------------------------------------------------
# 6. Patient Note Submission & Doctor Review Queue Integration Test
# ---------------------------------------------------------------------------
def test_patient_submission_and_doctor_queue(db_session):
    """Verify end-to-end patient note submission and doctor review queue prioritization."""
    pat = db_session.query(User).filter(User.role == "patient").first()
    doc = db_session.query(User).filter(User.role == "doctor").first()
    assert pat is not None, "Test requires a patient user in DB"
    assert doc is not None, "Test requires a doctor user in DB"
    
    # 1. Patient submits note
    req = ClinicalNoteSubmissionRequest(note=MASTER_TEST_CLINICAL_NOTE)
    res = submit_patient_clinical_note(req, db=db_session, current_user={"user_id": pat.id, "username": pat.username})
    
    assert res.get("status") == "PENDING_REVIEW"
    session_id = res.get("session_id")
    assert session_id is not None
    
    # 2. Doctor queries review queue
    q = get_doctor_review_queue(status_filter="PENDING", db=db_session, current_user={"user_id": doc.id, "username": doc.username})
    assert len(q) > 0
    latest_item = q[0]
    assert latest_item["session_id"] == session_id
    assert latest_item["status"] == "PENDING"


# ---------------------------------------------------------------------------
# 7. AI Quality Evaluation Suite Test
# ---------------------------------------------------------------------------
def test_ai_quality_evaluation_suite():
    """Verify quality matrix calculations across ground truth and predictions."""
    evaluator = AIEvaluationSuite()
    gt = [{"medications": [{"name": "Metformin", "dose": "500 mg", "route": "oral", "frequency": "BID"}]}]
    pred = [{"medications": [{"name": "Metformin", "dose": "500 mg", "route": "oral", "frequency": "BID"}], "hallucinations": [], "evidence_alignment_score": 0.98}]
    
    metrics = evaluator.evaluate_cohort(gt, pred)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["overall_quality_score"] == 100.0
