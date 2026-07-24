import pytest
from backend.agents.medication_safety_agent import MedicationSafetyAgent
from backend.agents.lab_interpretation_agent import LabInterpretationAgent
from backend.clinical.severity_risk_engine import SeverityRiskEngine
from backend.clinical.timeline_extractor import TimelineExtractor

def test_medication_safety_agent_duplicates_and_classes():
    meds = [
        {"name": "Paracetamol 500 mg", "dosage": "500 mg", "frequency": "Three Times Daily (TDS)"},
        {"name": "Paracetamol 650 mg", "dosage": "650 mg", "frequency": "Once Daily"},
        {"name": "Amlodipine", "dosage": "5 mg", "frequency": "Once Daily"}
    ]
    audit = MedicationSafetyAgent.audit_medications(meds)
    assert len(audit["duplicate_alerts"]) >= 1
    assert "Paracetamol" in audit["duplicate_alerts"][0]

    d_class, ind = MedicationSafetyAgent.get_drug_class_and_indication("Amlodipine")
    assert "Calcium Channel Blocker" in d_class
    assert "Hypertension" in ind

def test_lab_interpretation_agent_bnp():
    text = "Serum Creatinine: 2.2 mg/dL, BNP: 250 pg/mL, eGFR: 28 mL/min"
    interpreter = LabInterpretationAgent()
    labs = interpreter.interpret_labs(text)

    lab_names = [l["lab"] for l in labs]
    assert "BNP" in lab_names
    assert "Creatinine" in lab_names
    assert "eGFR" in lab_names

def test_multi_organ_risk_stratification():
    risks = SeverityRiskEngine.compute_organ_risk_stratification(
        diseases=["Hypertension", "Chronic Kidney Disease", "Pneumonia"],
        labs=["Creatinine: 2.2 mg/dL", "eGFR: 28 mL/min"],
        vitals=["BP: 150/95 mmHg"]
    )
    assert risks["stroke_risk"].upper() in ("HIGH", "MODERATE")
    assert risks["renal_failure_risk"].upper() in ("VERY HIGH", "HIGH")
    assert risks["respiratory_failure_risk"].upper() in ("VERY HIGH", "HIGH", "MODERATE")

def test_chronological_sequence_timeline():
    seq = TimelineExtractor.extract_chronological_sequence("Patient experienced fever on Day 1, cough on Day 3")
    assert len(seq) == 5
    assert seq[0]["day"] == "Day 1"
    assert seq[-1]["day"] == "Today"
