import pytest
from backend.clinical.medical_coder import MedicalCoder
from backend.agents.lab_interpretation_agent import LabInterpretationAgent
from backend.agents.relation_extraction_agent import compute_medication_validation, MedicationDetailModel

def test_cad_icd10_code_mapping():
    codes = MedicalCoder.get_disease_codes("Coronary Artery Disease")
    assert codes["icd10"] == "I25.10"
    assert codes["snomed"] == "53741008"

def test_egfr_ckd_stage_mismatch_detection():
    # Reported Stage III vs Calculated Stage IV (from eGFR 22)
    mismatch = LabInterpretationAgent.check_ckd_stage_mismatch("Patient has history of CKD Stage III", 22.0)
    assert mismatch is not None
    assert mismatch["reported_stage"] == "Stage III"
    assert mismatch["calculated_stage"] == "Stage IV"
    assert "Possible Stage Mismatch" in mismatch["warning"]

def test_itemized_medication_score_deductions():
    med = MedicationDetailModel(
        name="Paracetamol",
        disease_name="Fever",
        dosage="N/A",
        frequency="Once Daily",
        duration="N/A",
        route="Oral"
    )
    res = compute_medication_validation(med)
    assert res["completeness_score"] < 100
    assert "deduction_details" in res
    assert len(res["deduction_details"]) >= 2
    assert any("Missing Duration" in d for d in res["deduction_details"])
    assert any("Unspecified Dosage" in d for d in res["deduction_details"])
