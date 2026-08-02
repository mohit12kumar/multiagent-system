"""
tests/test_phase60_enterprise_blueprint.py

Comprehensive Test Suite for the 60-Phase Enterprise Architecture Refinement Pillars:
1. Workflow Engine with DAG Cycle Detection & Idempotency
2. 11-Dimensional Data Lineage & Provenance Tracker
3. Clinical Contradiction Guardrails & Hallucination Detector
4. Hierarchical Policy Engine & Knowledge Base Governance
5. FHIR R4 Bundle Mapper & Validation
6. AI Evaluation Suite & Quality Score Matrix
"""

import pytest
from backend.core.workflow_engine import WorkflowEngine, WorkflowNode, DAGCycleError
from backend.core.data_lineage import DataLineageTracker, ProvenanceVector
from backend.clinical.hallucination_detector import HallucinationDetector, ClinicalContradictionGuardrail
from backend.clinical.policy_engine import PolicyEngine
from backend.knowledge.knowledge_loader import KnowledgeLoader
from backend.interop.fhir_mapper import FHIRMapper, FHIRValidationError
from backend.clinical.ai_evaluator import AIEvaluationSuite
from backend.core.exceptions import ClinicalRuleError


# ── 1. Workflow Engine Tests ──────────────────────────────────────────────────

def test_workflow_dag_cycle_detection():
    """Verifies that WorkflowEngine detects cyclic dependencies and raises DAGCycleError."""
    engine = WorkflowEngine("CycleTest")
    
    node_a = WorkflowNode("A", lambda x: {"res": 1}, depends_on=["B"])
    node_b = WorkflowNode("B", lambda x: {"res": 2}, depends_on=["A"])
    
    engine.add_node(node_a).add_node(node_b)
    
    with pytest.raises(DAGCycleError):
        engine.detect_cycles()

def test_workflow_parallel_and_idempotent_execution():
    """Verifies parallel node execution and idempotent hash caching."""
    execution_counter = {"count": 0}

    def increment_handler(inputs):
        execution_counter["count"] += 1
        return {"val": inputs.get("val", 0) + 10}

    engine = WorkflowEngine("IdempotencyTest")
    n1 = WorkflowNode("step1", increment_handler, is_idempotent=True)
    engine.add_node(n1)

    # First Run
    res1 = engine.execute({"val": 5})
    assert res1["results"]["step1"]["val"] == 15
    assert execution_counter["count"] == 1
    assert "step1" in res1["executed_nodes"]

    # Second Run with identical inputs -> Should hit idempotency cache
    res2 = engine.execute({"val": 5})
    assert res2["results"]["step1"]["val"] == 15
    assert execution_counter["count"] == 1  # Handler NOT re-executed
    assert "step1" in res2["cached_nodes"]


# ── 2. Data Lineage & Provenance Tests ───────────────────────────────────────

def test_11_dimensional_data_lineage():
    """Verifies 11-Dimensional asset reproducibility vector and field SHA-256 provenance."""
    tracker = DataLineageTracker(document_id="DOC-99881", doc_version="v2.1")
    
    vec = ProvenanceVector(
        pipeline_version="v6.0.0",
        model_version="med-gemini-3.6",
        prompt_version="p_v3.2"
    )
    tracker.set_provenance_vector(vec)

    field_prov = tracker.add_field_provenance(
        field_name="metformin_dosage",
        field_value="500 mg",
        ocr_confidence=0.98,
        char_offsets=[45, 51]
    )

    report = tracker.export_lineage_report()
    
    assert report["document_id"] == "DOC-99881"
    assert report["11_dimensional_vectors"]["pipeline_version"] == "v6.0.0"
    assert len(report["field_provenance_chain"]) == 1
    assert field_prov.checksum is not None
    assert len(field_prov.checksum) == 64  # SHA-256 length


# ── 3. Clinical Contradiction & Hallucination Detector Tests ───────────────

def test_clinical_contradiction_male_pregnancy_rejection():
    """Verifies preflight rejection of Male + Pregnancy contradiction."""
    guardrail = ClinicalContradictionGuardrail()
    demographics = {"gender": "male"}
    clinical_data = {"conditions": ["pregnancy", "type 2 diabetes"]}

    with pytest.raises(ClinicalRuleError) as exc_info:
        guardrail.enforce_preflight_checks(demographics, clinical_data)

    assert "Clinical Contradiction Intercepted" in str(exc_info.value)
    assert "Pregnancy" in str(exc_info.value) or "pregnancy" in str(exc_info.value)

def test_clinical_contradiction_metformin_inhalation_rejection():
    """Verifies rejection of impossible route Metformin + Inhalation."""
    guardrail = ClinicalContradictionGuardrail()
    demographics = {"gender": "female"}
    clinical_data = {
        "medications": [{"name": "metformin", "route": "inhalation"}]
    }

    with pytest.raises(ClinicalRuleError):
        guardrail.enforce_preflight_checks(demographics, clinical_data)

def test_hallucination_detector_ungrounded_medication():
    """Verifies detection of ungrounded/hallucinated medications not present in raw text."""
    detector = HallucinationDetector()
    raw_note = "Patient has hypertension. Prescribed Lisinopril 10mg daily."
    extracted_data = {
        "medications": [
            {"name": "Lisinopril", "dose": "10mg"},
            {"name": "Atorvastatin", "dose": "20mg"}  # Not in note
        ]
    }

    res = detector.detect_hallucinations(raw_note, extracted_data)
    assert res["status"] == "FLAGGED"
    assert res["hallucination_rate"] > 0
    assert len(res["hallucinations"]) == 1
    assert res["hallucinations"][0]["entity"] == "atorvastatin"


# ── 4. Hierarchical Policy Engine Tests ──────────────────────────────────────

def test_hierarchical_policy_cascade():
    """Verifies multi-tier policy cascades (Hospital -> Department -> Doctor)."""
    engine = PolicyEngine()
    engine.register_doctor_policy("dr_smith", {"escalate_low_egfr": True, "min_confidence": 0.85})

    # Default Hospital Policy
    hosp_pol = engine.resolve_effective_policy()
    assert hosp_pol["min_confidence"] == 0.70

    # Department Policy (Nephrology)
    neph_pol = engine.resolve_effective_policy(department="nephrology")
    assert neph_pol["min_confidence"] == 0.80
    assert neph_pol["escalate_low_egfr"] is True

    # Doctor Override Policy
    doc_pol = engine.resolve_effective_policy(department="nephrology", doctor_id="dr_smith")
    assert doc_pol["min_confidence"] == 0.85


# ── 5. Knowledge Loader Governance Tests ──────────────────────────────────────

def test_knowledge_loader_governance_and_rollback():
    """Verifies status lifecycle management, version snapshots, and rollbacks."""
    loader = KnowledgeLoader()
    
    loader.set_approval_status("APPROVED", approver="Chief Medical Officer")
    assert loader.get_approval_status() == "APPROVED"

    # Take Snapshot v1
    snap_id = loader.create_version_snapshot("v1_stable", author="Admin")

    # Change status to DRAFT
    loader.set_approval_status("DRAFT", approver="Analyst")
    assert loader.get_approval_status() == "DRAFT"

    # Rollback to v1_stable
    success = loader.rollback_to_version("v1_stable")
    assert success is True
    assert loader.get_approval_status() == "APPROVED"
    assert len(loader.get_audit_log()) >= 3


# ── 6. FHIR R4 Mapper & Bundle Tests ────────────────────────────────────────

def test_fhir_r4_bundle_generation():
    """Verifies FHIR R4 Bundle creation and structural schema validation."""
    mapper = FHIRMapper()
    data = {
        "patient": {"id": "PAT-101", "name": "John Doe", "gender": "male"},
        "conditions": [{"name": "Type 2 Diabetes Mellitus", "icd10": "E11.9"}],
        "medications": [{"name": "Metformin", "dose": "500 mg", "route": "oral", "frequency": "BID"}],
        "labs": [{"test_name": "HbA1c", "val": 7.2, "unit": "%"}]
    }

    bundle = mapper.create_bundle(data, bundle_type="collection")
    
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert len(bundle["entry"]) == 4  # Patient + Condition + MedicationRequest + Observation

    # Schema Validation Pass
    assert mapper.validate_bundle_schema(bundle) is True

def test_fhir_schema_validation_failure():
    """Verifies FHIRValidationError is raised on invalid bundle structure."""
    mapper = FHIRMapper()
    invalid_bundle = {"resourceType": "NotABundle"}
    with pytest.raises(FHIRValidationError):
        mapper.validate_bundle_schema(invalid_bundle)


# ── 7. AI Evaluation Suite Tests ─────────────────────────────────────────────

def test_ai_evaluation_suite_metrics():
    """Verifies computation of all 9 quality matrix metrics."""
    evaluator = AIEvaluationSuite()
    
    gt = [
        {"medications": [{"name": "Metformin", "dose": "500 mg", "route": "oral", "frequency": "BID"}]}
    ]
    pred = [
        {
            "medications": [{"name": "Metformin", "dose": "500 mg", "route": "oral", "frequency": "BID"}],
            "hallucinations": [],
            "evidence_alignment_score": 1.0
        }
    ]

    metrics = evaluator.evaluate_cohort(gt, pred)

    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0
    assert metrics["hallucination_rate"] == 0.0
    assert metrics["dose_accuracy"] == 1.0
    assert metrics["overall_quality_score"] == 100.0
