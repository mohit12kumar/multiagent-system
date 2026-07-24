import pytest
from backend.agents.regex_agent import RegexAgent
from backend.agents.lab_interpretation_agent import LabInterpretationAgent
from backend.agents.contraindication_agent import ContraindicationAgent
from backend.agents.medication_safety_agent import MedicationSafetyAgent
from backend.agents.clinical_consistency_agent import ClinicalConsistencyAgent
from backend.clinical.differential_diagnosis_engine import DifferentialDiagnosisEngine
from backend.clinical.severity_risk_engine import SeverityRiskEngine
from backend.clinical.medical_coder import MedicalCoder

TEST_CASE_2_TEXT = """
Patient Name: Michael Thompson, Age: 71 years, Gender: Male.
Chief Complaint: Severe chest pain radiating to the left arm for 2 hours, increasing shortness of breath, productive cough with yellow sputum, fever, chills, bilateral leg swelling, orthopnea, confusion, nausea, vomiting, decreased urine output.
Past Medical History: Hypertension (2007), Type 2 Diabetes Mellitus (2010), Coronary Artery Disease with PCI (2019), Heart Failure with Reduced Ejection Fraction, Chronic Kidney Disease Stage III (reported), COPD, Hyperlipidemia, GERD.
Smoking: 50 pack-year smoker. Quit in 2023.
Current Medications: Metphormin 1000 mg TDS, Losartan 100 mg OD, Amlodpine 10 mg OD, Atrovastatin 40 mg HS, Aspirin 75 mg OD, Clopidogrel 75 mg OD, Furosemid 40 mg BD, Omeprazol 20 mg OD, Salbutmol inhaler SOS, Ceftriaxone 1 g IV BD, Azithromicin 500 mg OD, Paracetmol 650 mg TDS.
Allergies: Penicillin, Sulfa.
Vitals: BP 184/112, HR 126, RR 34, SpO2 82%, Temp 103.1°F.
Labs: Troponin-I 8.4 ng/mL, BNP 2800 pg/mL, Creatinine 4.1 mg/dL, eGFR 16 mL/min, Potassium 6.7 mmol/L, Sodium 128, HbA1c 10.8%, CRP 28, WBC 24.6, Hemoglobin 8.9, LDL 201 mg/dL, HDL 29 mg/dL, Triglycerides 312 mg/dL, Lactate 4.6 mmol/L, D-dimer 2200 ng/mL.
ECG: Acute ST elevation in II III aVF, Reciprocal ST depression, Frequent PVCs.
Chest X-ray: Pulmonary edema, Right lower lobe consolidation. Echo: EF 22%.
Assessment: Acute Inferior STEMI, Acute Decompensated Heart Failure, Pulmonary Edema, Community Acquired Pneumonia, Acute Kidney Injury on CKD, Hyperkalemia, Poorly Controlled Diabetes, Severe Hypertension, Hyperlipidemia.
"""

def test_disease_deduplication_canonical_normalization():
    # STEMI and MI must merge into single canonical disease node
    diseases = ["STEMI", "Acute STEMI", "Acute Inferior STEMI", "Acute Myocardial Infarction", "MI"]
    merged = DifferentialDiagnosisEngine.merge_duplicate_diagnoses(diseases)
    assert len(merged) == 1
    assert merged[0] == "Acute Inferior STEMI / Acute Myocardial Infarction"

    chf_diseases = ["CHF", "Congestive Heart Failure", "Heart Failure", "HFrEF"]
    merged_chf = DifferentialDiagnosisEngine.merge_duplicate_diagnoses(chf_diseases)
    assert len(merged_chf) == 1
    assert merged_chf[0] == "Heart Failure"

    lipid_diseases = ["Hyperlipidemia", "Dyslipidemia", "Hyperlipidaemia"]
    merged_lipid = DifferentialDiagnosisEngine.merge_duplicate_diagnoses(lipid_diseases)
    assert len(merged_lipid) == 1
    assert merged_lipid[0] == "Hyperlipidemia"

def test_icd10_and_snomed_codes():
    codes_hyperkalemia = MedicalCoder.get_disease_codes("Hyperkalemia")
    assert codes_hyperkalemia["icd10"] == "E87.5"

    codes_aki = MedicalCoder.get_disease_codes("Acute Kidney Injury")
    assert codes_aki["icd10"] == "N17.9"

    codes_cad = MedicalCoder.get_disease_codes("Coronary Artery Disease")
    assert codes_cad["icd10"] == "I25.10"

    codes_stemi = MedicalCoder.get_disease_codes("Acute STEMI")
    assert codes_stemi["icd10"] == "I21.19"

    codes_depression = MedicalCoder.get_disease_codes("Depression")
    assert codes_depression["icd10"] == "F32.9"

def test_egfr_14_stage_v_mismatch_calculator():
    mismatch = LabInterpretationAgent.check_ckd_stage_mismatch(TEST_CASE_2_TEXT, egfr_val=14.0)
    assert mismatch is not None
    assert "Stage V" in mismatch["warning"]
    assert "Reported: Stage III" in mismatch["warning"]

def test_metformin_and_losartan_contraindications():
    agent = ContraindicationAgent()
    warnings = agent.check_contraindications(
        ["Metformin", "Losartan"],
        ["Chronic Kidney Disease", "Hyperkalemia"],
        ["Penicillin", "Sulfa"]
    )
    warn_drugs = [w["drug"].lower() for w in warnings]
    assert "metformin" in warn_drugs
    assert "losartan" in warn_drugs

def test_medication_safety_audit():
    audit = MedicationSafetyAgent.audit_medications([
        {"name": "Atorvastatin", "dosage": "40mg"},
        {"name": "Rosuvastatin", "dosage": "20mg"},
        {"name": "Aspirin", "dosage": "75mg"},
        {"name": "Clopidogrel", "dosage": "75mg"}
    ])
    alerts = " ".join(audit["duplicate_alerts"])
    assert "Duplicate Statin Therapy" in alerts
    assert "Dual Antiplatelet Therapy" in alerts

def test_organ_risk_stratification():
    risks = SeverityRiskEngine.compute_organ_risk_stratification(
        diseases=["Acute STEMI", "Heart Failure", "Hyperkalemia", "Pulmonary Edema", "Community Acquired Pneumonia"],
        labs=["Troponin-I 8.4 ng/mL", "BNP 2800 pg/mL", "Creatinine 4.1 mg/dL", "Potassium 6.7 mmol/L", "WBC 24.6"],
        vitals=["BP 184/112", "SpO2 82%", "Temp 103.1°F"]
    )
    assert risks["cardiac_risk"] == "VERY HIGH"
    assert risks["renal_failure_risk"] == "VERY HIGH"
    assert risks["respiratory_failure_risk"] == "VERY HIGH"
    assert risks["stroke_risk"] == "HIGH"
    assert risks["sepsis_risk"] == "HIGH"
    assert risks["overall_risk_level"] == "CRITICAL"

def test_clinical_consistency_and_confidence_bands():
    is_valid, msg, score, sup, conf, band = ClinicalConsistencyAgent.validate_consistency(
        disease_name="Acute STEMI",
        symptoms=["chest pain"],
        medications=[],
        labs=[{"lab": "troponin"}],
        vitals=[]
    )
    assert is_valid is True
    assert band in ("Confirmed", "High Confidence")
    assert len(sup) >= 1
