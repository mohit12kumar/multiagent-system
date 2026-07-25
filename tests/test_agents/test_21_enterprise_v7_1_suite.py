import pytest
from backend.clinical.clinical_validation_engine import ClinicalValidationEngine
from backend.clinical.explainable_ai_engine import ExplainableAIEngine
from backend.clinical.medication_optimization_engine import MedicationOptimizationEngine
from backend.clinical.differential_diagnosis_engine import DifferentialDiagnosisEngine
from backend.clinical.clinical_pathway_engine import ClinicalPathwayEngine
from backend.clinical.clinical_completeness_engine import ClinicalCompletenessEngine

def test_clinical_validation_engine_structured_report():
    report = ClinicalValidationEngine.validate_clinical_record(
        diseases=["Acute Inferior STEMI", "Heart Failure"],
        medications=[{"name": "Aspirin"}],
        labs=[{"name": "Troponin-I", "value": "8.6"}],
        vitals=[{"name": "Blood Pressure", "value": "168/102"}],
        imaging=[{"name": "ECG", "value": "ST Elevation"}]
    )
    res = report["clinical_validation"]
    
    assert res["overall_score"] > 0
    assert "warnings" in res
    assert "missing_items" in res
    assert "critical_missing" in res

def test_explainable_ai_engine_weights_breakdown():
    explain = ExplainableAIEngine.calculate_explainable_confidence(
        disease_name="Acute Inferior STEMI",
        symptoms=["chest pain"],
        labs=[{"name": "Troponin-I", "value": "8.6"}],
        vitals=[],
        imaging=[{"name": "ECG", "value": "ST Elevation"}]
    )
    cb = explain["confidence_breakdown"]
    
    assert len(cb["positive"]) >= 2
    assert cb["final_score"] >= 90
    assert any("Troponin" in p["factor"] for p in cb["positive"])

def test_medication_optimization_engine_alternatives_and_monitoring():
    opts = MedicationOptimizationEngine.optimize_medications(
        medications=[{"name": "Metformin 1000 mg"}, {"name": "Losartan 100 mg"}],
        diseases=["Acute Kidney Injury", "Hyperkalemia"],
        labs=[{"lab": "eGFR", "value": "15"}, {"lab": "Potassium", "value": "6.8"}]
    )
    
    assert len(opts) == 2
    met_opt = next(o for o in opts if o["drug"] == "Metformin 1000 mg")
    assert met_opt["status"] == "Stop"
    assert "Insulin" in met_opt["alternative"]
    assert len(met_opt["monitoring"]) >= 2
    assert met_opt["guideline"] == "ADA 2025 Standard of Care"

def test_differential_diagnosis_engine_ranking():
    diff = DifferentialDiagnosisEngine.evaluate_differential_diagnoses("Severe Central Chest Pain")
    diffs = diff["differential_diagnoses"]
    
    assert diff["chief_complaint"] == "Severe Central Chest Pain"
    assert len(diffs) >= 2
    stemi_diff = diffs[0]
    assert stemi_diff["disease"] == "Acute Inferior STEMI"
    assert stemi_diff["probability"] == 0.94
    assert len(stemi_diff["supporting_evidence"]) >= 2

def test_clinical_pathway_engine_timeframes():
    pathway = ClinicalPathwayEngine.get_pathway_for_disease("Acute Inferior STEMI")
    timeframes = [p["timeframe"] for p in pathway]
    
    assert "0 min" in timeframes
    assert "15 min" in timeframes
    assert "30 min" in timeframes
    assert "60 min" in timeframes

def test_clinical_completeness_engine_checklist():
    text = "Patient has past medical history of DM. Vitals: BP 160/90. Labs: Troponin 8.6, BNP 2950, Creatinine 4.2. Imaging: ECG ST Elevation. Meds: Aspirin. Follow-up in 24 hours."
    chk = ClinicalCompletenessEngine.evaluate_completeness(
        text=text,
        diseases=["STEMI"],
        medications=["Aspirin"],
        labs=["Troponin", "BNP", "Creatinine"],
        imaging=["ECG"]
    )
    checklist = chk["clinical_completeness_checklist"]
    
    assert checklist["history"] == "✓"
    assert checklist["examination"] == "✓"
    assert checklist["laboratories"] == "✓"
    assert checklist["imaging"] == "✓"
    assert checklist["medications"] == "✓"
    assert checklist["follow_up"] == "✓"
    assert chk["checklist_score"] == "100%"
