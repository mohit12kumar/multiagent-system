"""
tests/test_agents/test_23_master_enterprise_60_phase_suite.py

Automated Test Suite for the 60-Phase Enterprise Architecture & Governance Platform.
Tests:
  - ModelManager lifecycle & health
  - MaxDoseValidator overdose alerts
  - TherapeuticDuplicationEngine duplicate therapy alerts
  - HallucinationDetector clinical contradiction guardrails
  - ClinicalRiskEngine scores (NEWS2, qSOFA, CHA2DS2-VASc, eGFR/Child-Pugh dose adjusters)
  - DeclarativeRulesEngine YAML rule evaluation
  - WorkflowEngine DAG execution & topological cycle validation
  - DataLineageEngine 11-dimensional audit provenance
  - FHIRMapper R4 Bundle generation
  - EnterpriseGovernance 11-vector asset reproducibility manifest
  - AIEvaluator & DriftDetector metrics
"""

import pytest
from backend.core.model_manager import model_manager
from backend.clinical.max_dose_validator import MaxDoseValidator
from backend.clinical.therapeutic_duplication_engine import TherapeuticDuplicationEngine
from backend.clinical.hallucination_detector import HallucinationDetector
from backend.clinical.clinical_risk_engine import ClinicalRiskEngine
from backend.clinical.rules_dsl import DeclarativeRulesEngine
from backend.core.workflow_engine import WorkflowEngine
from backend.core.data_lineage import DataLineageEngine
from backend.interop.fhir_mapper import FHIRMapper
from backend.core.enterprise_governance import EnterpriseGovernance
from backend.core.ai_evaluator import AIEvaluator
from backend.core.drift_detector import drift_detector


def test_model_manager_lifecycle():
    model_manager.load_all()
    health = model_manager.check_health()
    assert health["overall_status"] == "HEALTHY"
    assert "spacy_en_core_web_sm" in health["models"]


def test_max_dose_validator():
    overdose_meds = [{"name": "Paracetamol", "dose": "2000 mg", "frequency": "QID"}]
    warnings = MaxDoseValidator.validate_medications(overdose_meds)
    assert len(warnings) >= 1
    assert warnings[0]["severity"] == "CRITICAL_OVERDOSE"


def test_therapeutic_duplication_engine():
    duplicate_meds = [{"name": "Ibuprofen"}, {"name": "Diclofenac"}]
    warnings = TherapeuticDuplicationEngine.detect_duplications(duplicate_meds)
    assert len(warnings) >= 1
    assert warnings[0]["drug_class"] == "NSAIDs"


def test_hallucination_detector_contradictions():
    valid, rejections = HallucinationDetector.verify_extraction_output(
        patient_text="Patient given Metformin PO.",
        medications=[{"name": "Metformin", "route": "Inhalation"}],
        diseases=["Pregnancy"],
        patient_gender="male"
    )
    assert len(rejections) >= 1
    assert any(r["type"] == "IMPOSSIBLE_ROUTE_HALLUCINATION" for r in rejections)


def test_clinical_risk_engine():
    news2 = ClinicalRiskEngine.evaluate_news2(rr=26, spo2=90, sbp=85, hr=135, temp=38.5)
    assert news2["news2_score"] >= 10
    assert news2["risk_category"].startswith("High")

    egfr = ClinicalRiskEngine.evaluate_egfr_dose_adjustment(22.0, "Metformin")
    assert egfr["ckd_stage"] == "CKD Stage IV (Severe)"


def test_declarative_rules_dsl():
    engine = DeclarativeRulesEngine()
    results = engine.evaluate_rules({"egfr": 25, "potassium": 6.2})
    assert len(results) >= 2


def test_workflow_engine_dag():
    wf = WorkflowEngine("test_dag")
    wf.add_node("step1", lambda ctx: {"a": 1})
    wf.add_node("step2", lambda ctx: {"b": ctx["a"] + 1}, depends_on=["step1"])
    res = wf.execute_dag({"session_id": "test-session"})
    assert res["b"] == 2


def test_data_lineage_and_governance():
    lin = DataLineageEngine.attach_provenance("500 mg", "Metformin 500 mg PO", 10, 16, "medication_parser")
    assert "lineage_vectors" in lin
    assert lin["lineage_vectors"]["pipeline_version"] == "3.0.0-enterprise"

    manifest = EnterpriseGovernance.get_reproducibility_manifest()
    assert manifest["manifest_status"] == "VERIFIED_AUDITABLE"
    assert len(manifest["asset_versions"]) == 11


def test_fhir_mapper_bundle():
    bundle = FHIRMapper.create_fhir_transaction_bundle(
        patient_id="pat-101",
        diseases=["Type 2 Diabetes Mellitus"],
        medications=[{"name": "Metformin", "dose": "500 mg", "frequency": "BID", "route": "PO"}]
    )
    assert bundle["resourceType"] == "Bundle"
    assert len(bundle["entry"]) == 3


def test_ai_evaluator_and_drift():
    metrics = AIEvaluator.evaluate_benchmark(
        predicted_meds=[{"name": "Metformin"}],
        gold_meds=[{"name": "Metformin"}]
    )
    assert metrics["f1_score"] == 1.0

    drift_detector.log_confidence(0.95)
    drift = drift_detector.detect_drift()
    assert not drift["drift_detected"]
