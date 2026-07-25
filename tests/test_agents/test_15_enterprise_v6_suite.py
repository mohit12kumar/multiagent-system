import pytest
from backend.engines.normalization_engine import NormalizationEngine
from backend.engines.terminology_service import TerminologyService
from backend.engines.evidence_engine import EvidenceEngine
from backend.engines.disease_engine import DiseaseEngine
from backend.engines.risk_engine import RiskEngine
from backend.engines.predictive_risk_engine import PredictiveRiskEngine
from backend.engines.lab_vital_trend_engine import LabVitalTrendEngine
from backend.engines.fhir_engine import FHIREngine
from backend.engines.clinical_graph_engine import ClinicalGraphEngine
from backend.engines.audit_engine import AuditEngine
from backend.engines.observability_engine import ObservabilityEngine
from backend.engines.security_engine import SecurityEngine
from backend.agents.formatting_agent import FormattingAgent
from backend.models.pipeline_state import PipelineState
from src.models.entity import EntityMentionModel

def test_01_normalization_and_terminology_service():
    norm_d = NormalizationEngine.normalize_disease("mi")
    assert norm_d == "Acute Inferior STEMI"

    codes = TerminologyService.get_disease_codes("Acute Inferior STEMI")
    assert codes["icd10"] == "I21.19"
    assert codes["snomed"] == "4013007"

    lab_code = TerminologyService.get_lab_code("Troponin")
    assert lab_code["loinc"] == "10839-9"

def test_02_evidence_and_risk_engines():
    ev = EvidenceEngine.evaluate_evidence(
        labs=[{"name": "Troponin", "value": "8.4 ng/mL"}],
        vitals=[{"name": "SpO2", "value": "82%"}],
        symptoms=["Chest pain"],
        medications=[{"name": "Aspirin"}]
    )
    assert len(ev["primary"]) >= 1
    assert len(ev["secondary"]) >= 1

    risk = RiskEngine.compute_organ_risk(["Acute Inferior STEMI"], [{"lab": "Troponin", "value": "8.4"}], [])
    assert risk["cardiac"] == "VERY HIGH"
    assert risk["overall"] == "CRITICAL"

def test_03_predictive_risk_engine():
    preds = PredictiveRiskEngine.predict_all_outcomes(["Diabetes Mellitus"], [{"lab": "Creatinine", "value": "4.1"}], [])
    assert "Chronic Kidney Disease" in preds["future_disease_risks"]
    assert "readmission" in preds
    assert "icu_decompensation" in preds
    assert "mortality" in preds

def test_04_fhir_engine_and_networkx_graph():
    fhir = FHIREngine.build_fhir_bundle("PATIENT-123", [{"name": "STEMI", "icd10": "I21.19"}], [{"name": "Aspirin"}], [{"lab": "Troponin", "value": "8.4"}])
    assert fhir["resourceType"] == "Bundle"
    assert fhir["total_resources"] >= 4

    graph = ClinicalGraphEngine.build_networkx_graph("PATIENT-123", [{"name": "STEMI"}], ["Chest pain"], [{"name": "Aspirin"}], [], [])
    assert graph["graph_type"] == "NetworkX Directed Multi-Relational Graph"
    assert graph["node_count"] >= 3

def test_05_dynamic_disease_plugin_loader():
    res = DiseaseEngine.evaluate_disease("Acute Inferior STEMI", ["Chest pain"], [], [])
    assert res["plugin_executed"] is True
    assert res["icd10"] == "I21.19"
    assert "ACC/AHA" in [g["organization"] for g in res["guidelines"]]

def test_06_master_formatting_agent_v6_schema():
    state = PipelineState(
        session_id="test_v6_sess",
        document_id="test_v6_doc",
        text="2012 Hypertension, 2014 Diabetes. Troponin 8.4 ng/mL, Potassium 6.7 mmol/L, eGFR 16 mL/min. Aspirin, Metformin prescribed."
    )
    state.final_entities = [
        EntityMentionModel(text="Acute Inferior STEMI", type="DISEASE", start_char=0, end_char=20),
        EntityMentionModel(text="Aspirin", type="DRUG", start_char=21, end_char=28)
    ]
    agent = FormattingAgent()
    res = agent.process(state)

    # Verify key v6.0 response fields
    assert "networkx_graph" in res
    assert "fhir_bundle" in res
    assert "predictive_risks" in res
    assert "lab_vital_trends" in res
    assert "medico_legal_citations" in res
    assert "observability" in res
    assert "security" in res
    assert res["security"]["hipaa_audit_log_id"].startswith("AUDIT-HIPAA")
