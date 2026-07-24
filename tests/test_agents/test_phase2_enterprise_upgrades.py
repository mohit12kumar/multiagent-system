import pytest
from backend.agents.clinical_consistency_agent import ClinicalConsistencyAgent
from backend.agents.rag_agent import RAGAgent
from backend.clinical.differential_diagnosis_engine import DifferentialDiagnosisEngine

def test_clinical_consistency_agent_validation():
    # Valid pneumonia with symptoms
    is_ok, reason, score, sup, conf, band = ClinicalConsistencyAgent.validate_consistency(
        "Community Acquired Pneumonia",
        ["cough", "fever"],
        [{"name": "Azithromycin"}],
        [{"lab": "WBC"}],
        []
    )
    assert is_ok is True
    assert score >= 0.70

    # Invalid pneumonia without symptoms/labs/meds
    is_invalid, inv_reason, inv_score, inv_sup, inv_conf, inv_band = ClinicalConsistencyAgent.validate_consistency(
        "Community Acquired Pneumonia",
        [],
        [],
        [],
        []
    )
    assert is_invalid is False
    assert "Insufficient supporting evidence" in inv_reason

def test_merge_duplicate_diagnoses():
    raw_list = ["HTN", "Hypertension", "Essential Hypertension", "Type 2 Diabetes", "T2DM"]
    merged = DifferentialDiagnosisEngine.merge_duplicate_diagnoses(raw_list)
    assert len(merged) == 2
    assert "Hypertension" in merged
    assert "Type 2 Diabetes Mellitus" in merged

def test_rag_guideline_attributions():
    rag = RAGAgent()
    attributions = rag.get_guideline_attributions(["Chronic Kidney Disease", "Hypertension"])
    assert len(attributions) >= 1
    assert "KDIGO" in attributions[0]["guideline"] or "ACC/AHA" in attributions[0]["guideline"]
