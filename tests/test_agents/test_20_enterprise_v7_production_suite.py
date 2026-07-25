import pytest
from backend.api.health_monitoring_router import HealthMonitoringRouter
from backend.engines.fhir_engine import FHIREngine
from backend.clinical.evaluation_benchmark_suite import EvaluationBenchmarkSuite

def test_health_monitoring_router_liveness_and_readiness():
    health = HealthMonitoringRouter.get_health_status()
    ready = HealthMonitoringRouter.get_readiness_status()
    
    assert health["status"] == "HEALTHY"
    assert health["version"] == "7.0.0"
    assert ready["status"] == "READY"
    assert ready["subsystems"]["nlp_extraction_engine"] == "OPERATIONAL"
    assert ready["subsystems"]["fhir_r4_validator"] == "ACTIVE"

def test_fhir_r4_schema_validation_and_bidirectional_import():
    bundle = FHIREngine.build_fhir_bundle(
        patient_id="pt_v7_01",
        diseases=[{"name": "Acute Inferior STEMI", "icd10": "I21.1", "snomed": "371087003"}],
        medications=[{"name": "Aspirin"}],
        labs=[{"name": "Troponin-I", "value": "8.6 ng/mL"}]
    )
    
    assert bundle["resourceType"] == "Bundle"
    assert bundle["validation"]["valid"] is True
    assert bundle["validation"]["schema_version"] == "FHIR R4 (4.0.1)"
    
    imported = FHIREngine.import_fhir_bundle(bundle)
    assert imported["status"] == "FHIR_IMPORT_SUCCESS"
    assert "Acute Inferior STEMI" in imported["imported_diseases"]
    assert "Aspirin" in imported["imported_medications"]
    assert len(imported["imported_labs"]) == 1

def test_evaluation_benchmark_suite_precision_recall_f1():
    metrics = EvaluationBenchmarkSuite.run_benchmark_evaluation()
    
    assert metrics["evaluation_status"] == "BENCHMARK_COMPLETE"
    assert metrics["disease_metrics"]["f1_score"] >= 95.0
    assert metrics["medication_metrics"]["f1_score"] >= 95.0
    assert metrics["production_ready"] is True
