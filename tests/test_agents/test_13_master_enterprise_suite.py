import pytest
from backend.clinical.clinical_knowledge_graph import ClinicalKnowledgeGraph
from backend.clinical.evidence_confidence_engine import EvidenceConfidenceEngine
from backend.clinical.severity_risk_engine import SeverityRiskEngine
from backend.clinical.clinical_rule_engine import ClinicalRuleEngine
from backend.clinical.medication_effectiveness_engine import MedicationEffectivenessEngine
from backend.clinical.quality_score_engine import QualityScoreEngine
from backend.clinical.missing_info_auditor import MissingInfoAuditor
from backend.agents.contraindication_agent import ContraindicationAgent
from backend.agents.formatting_agent import FormattingAgent
from backend.models.pipeline_state import PipelineState
from src.models.entity import EntityMentionModel

def test_01_disease_confidence_explanation_and_ranking():
    res = EvidenceConfidenceEngine.calculate_disease_confidence(
        disease_name="Acute Inferior STEMI",
        symptoms=["Chest pain", "Shortness of breath"],
        medication_present=True,
        vitals_present=True,
        labs_present=True,
        imaging_present=True
    )
    assert res["score"] >= 95
    assert res["band"] == "Confirmed"
    assert len(res["reasoning"]) >= 4
    assert "ranked_evidence" in res
    assert "primary" in res["ranked_evidence"]

def test_02_disease_stage_severity_and_progression():
    stage = ClinicalKnowledgeGraph.calculate_disease_stage("Chronic Kidney Disease", [{"lab": "eGFR", "value": "16"}], [])
    assert "Stage IV" in stage

    sev, reason = SeverityRiskEngine.evaluate_severity("Acute Inferior STEMI", ["Chest pain"], [], [{"lab": "Troponin", "value": "8.4"}])
    assert "Critical" in sev

def test_03_clinical_rule_engine_and_terminology_mappings():
    alerts = ClinicalRuleEngine.evaluate_lab_thresholds([
        {"lab": "Troponin", "value": "8.4 ng/mL"},
        {"lab": "Potassium", "value": "6.7 mmol/L"}
    ])
    assert len(alerts) >= 2
    assert any(a["marker"] == "Troponin" for a in alerts)
    assert any(a["marker"] == "Potassium" for a in alerts)

def test_04_medication_effectiveness_and_monitoring():
    eff = MedicationEffectivenessEngine.evaluate_medication("Metformin", "Diabetes Mellitus")
    assert eff["evidence_supports_disease"] is True
    assert "HbA1c" in eff["monitoring_markers"]
    assert "Lactic Acidosis" in eff["adr_prediction"]["risk"]

def test_05_quality_score_and_missing_info_audit():
    qs = QualityScoreEngine.calculate_quality_score(["STEMI"], ["Aspirin"], [{"lab": "Troponin", "value": "8.4"}], [])
    assert "overall_score" in qs
    assert "breakdown" in qs

    mi = MissingInfoAuditor.audit_missing_information("Patient with STEMI.", ["STEMI"], [], [], [])
    assert "history" in mi
    assert "critical" in mi

def test_06_master_formatting_agent_schema():
    state = PipelineState(
        session_id="test_master_sess",
        document_id="test_master_doc",
        text="2012 Hypertension, 2014 Diabetes. Troponin 8.4 ng/mL, Potassium 6.7 mmol/L, eGFR 16 mL/min. Aspirin, Metformin prescribed."
    )
    state.final_entities = [
        EntityMentionModel(text="Acute Inferior STEMI", type="DISEASE", start_char=0, end_char=20),
        EntityMentionModel(text="Aspirin", type="DRUG", start_char=21, end_char=28)
    ]
    agent = FormattingAgent()
    res = agent.process(state)

    # Verify key dynamic enterprise response schema fields
    assert "patient_summary" in res
    assert "diseases" in res
    assert "organ_risk" in res
    assert "medication_validation" in res
    assert "contraindications" in res
    assert "timeline" in res
    assert "missing_information" in res
    assert "quality_score_breakdown" in res
    assert "rule_alerts" in res
    assert "medication_effectiveness" in res
    assert "audit" in res
    assert "metadata" in res
