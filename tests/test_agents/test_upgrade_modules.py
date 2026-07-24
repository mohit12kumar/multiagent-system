import pytest
from backend.models.pipeline_state import PipelineState
from backend.models.entity import EntityMentionModel
from backend.agents.relation_extraction_agent import RelationExtractionAgent, infer_formulation, infer_route
from backend.agents.dosage_validation_agent import DosageValidationAgent
from backend.clinical.evidence_confidence_engine import EvidenceConfidenceEngine

def test_dosage_validation_agent():
    # Valid Azithromycin
    ok, warn = DosageValidationAgent.validate("Azithromycin", "500 mg", "PO (Oral)", "Tablet")
    assert ok is True
    assert warn is None

    # Flagged high dose Azithromycin
    ok_high, warn_high = DosageValidationAgent.validate("Azithromycin", "650 mg", "PO (Oral)", "Tablet")
    assert ok_high is False
    assert warn_high is not None
    assert "High dose" in warn_high or "Non-standard" in warn_high

    # Incompatible Omeprazole 2 puffs
    ok_puff, warn_puff = DosageValidationAgent.validate("Omeprazole", "2 puffs", "Inhalation", "Inhaler")
    assert ok_puff is False
    assert warn_puff is not None
    assert "Incompatible formulation" in warn_puff

def test_formulation_and_route_inference():
    f_inhaler = infer_formulation("Salbutamol Inhaler", "2 puffs twice daily")
    assert f_inhaler == "Inhaler"
    r_inhaler = infer_route("Salbutamol", f_inhaler, "2 puffs")
    assert r_inhaler == "Inhalation"

    f_tab = infer_formulation("Tab Omeprazole", "20 mg before breakfast")
    assert f_tab == "Tablet"
    r_tab = infer_route("Omeprazole", f_tab, "20 mg")
    assert r_tab == "PO (Oral)"

def test_dynamic_confidence_engine():
    conf_data = EvidenceConfidenceEngine.calculate_disease_confidence(
        disease_name="Pneumonia",
        symptoms=["cough", "fever"],
        medication_present=True,
        vitals_present=True,
        labs_present=True,
        assessment_present=True,
        history_present=True
    )
    conf = conf_data["overall_confidence"]
    assert 0.50 <= conf <= 0.99
    assert len(conf_data["detected_because"]) >= 4
