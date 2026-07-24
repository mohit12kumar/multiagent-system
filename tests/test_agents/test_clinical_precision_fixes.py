import pytest
from backend.agents.relation_extraction_agent import expand_frequency, infer_route, compute_medication_validation
from backend.models.relation import MedicationDetailModel
from backend.clinical.severity_risk_engine import SeverityRiskEngine

def test_frequency_abbreviation_expansion():
    assert expand_frequency("TDS") == "Three Times Daily (TDS)"
    assert expand_frequency("TID") == "Three Times Daily (TID)"
    assert expand_frequency("BD") == "Twice Daily (BD)"
    assert expand_frequency("BID") == "Twice Daily (BID)"
    assert expand_frequency("QID") == "Four Times Daily (QID)"
    assert expand_frequency("PRN") == "As Needed (PRN)"

def test_oral_route_enforcement():
    # Omeprazole and Azithromycin should infer PO (Oral), not Inhalation
    r_omep = infer_route("Omeprazole", "Tablet", "Patient takes Omeprazole 20 mg PO daily")
    assert r_omep == "PO (Oral)"

    r_azi = infer_route("Azithromycin", "Tablet", "Azithromycin 500 mg PO for 5 days")
    assert r_azi == "PO (Oral)"

    r_salb = infer_route("Salbutamol", "Inhaler", "Salbutamol 2 puffs inhalation as needed")
    assert r_salb == "Inhalation"

def test_dynamic_completeness_scoring_and_explanations():
    med_full = MedicationDetailModel(
        name="Azithromycin",
        dosage="500 mg",
        frequency="Once Daily",
        route="PO (Oral)",
        duration="5 Days",
        formulation="Tablet"
    )
    val_full = compute_medication_validation(med_full)
    assert val_full["completeness_score"] == 100

    med_missing_dur = MedicationDetailModel(
        name="Omeprazole",
        dosage="20 mg",
        frequency="Once Daily",
        route="PO (Oral)",
        duration="Duration Not Specified",
        formulation="Tablet"
    )
    val_missing = compute_medication_validation(med_missing_dur)
    assert val_missing["completeness_score"] < 100
    assert "Missing Duration" in val_missing["explanations"]

def test_hypertension_severity_evaluation():
    sev, reason = SeverityRiskEngine.evaluate_severity(
        "Hypertension",
        ["headache"],
        ["BP: 150/95 mmHg"],
        []
    )
    assert any(expected in sev for expected in ("Severe", "Moderate", "Stage 2"))
    assert "Hypertension" in reason or "Stage" in reason
