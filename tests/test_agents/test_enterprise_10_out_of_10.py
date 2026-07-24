import pytest
from backend.agents.regex_agent import RegexAgent
from backend.agents.lab_interpretation_agent import LabInterpretationAgent
from backend.agents.contraindication_agent import ContraindicationAgent
from backend.clinical.severity_risk_engine import SeverityRiskEngine

def test_critical_diseases_regex_extraction():
    agent = RegexAgent()
    sentences = [{"text": "Patient has acute myocardial infarction, congestive heart failure, hyperkalemia, and pulmonary edema."}]
    entities = agent.extract(sentences)
    disease_texts = [e.text.lower() for e in entities if e.type == "DISEASE"]

    assert any("myocardial infarction" in d for d in disease_texts)
    assert any("heart failure" in d for d in disease_texts)
    assert any("hyperkalemia" in d for d in disease_texts)
    assert any("pulmonary edema" in d for d in disease_texts)

def test_critical_lab_interpretation():
    interpreter = LabInterpretationAgent()
    text = "Troponin: 4.5 ng/mL, BNP: 1650 pg/mL, Potassium: 6.1 mmol/L"
    labs = interpreter.interpret_labs(text)

    lab_map = {l["lab"]: l for l in labs}
    assert "Troponin" in lab_map
    assert "Acute Myocardial Infarction" in lab_map["Troponin"]["supporting_disease"]
    assert "Heart Failure" in lab_map["BNP"]["supporting_disease"]
    assert lab_map["Potassium"]["interpretation"] == "Hyperkalemia"

def test_metformin_and_losartan_contraindications():
    agent = ContraindicationAgent()
    # Metformin with CKD / eGFR 21 and Losartan with Hyperkalemia
    warnings = agent.check_contraindications(
        ["Metformin", "Losartan"],
        ["Chronic Kidney Disease", "Hyperkalemia"],
        []
    )
    w_meds = [w["drug"].lower() for w in warnings]
    assert "metformin" in w_meds
    assert "losartan" in w_meds

def test_critical_organ_risk_stratification():
    risks = SeverityRiskEngine.compute_organ_risk_stratification(
        diseases=["Acute Myocardial Infarction", "Congestive Heart Failure", "Hyperkalemia"],
        labs=["Troponin: 4.5 ng/mL", "BNP: 1650 pg/mL", "Potassium: 6.1 mmol/L"],
        vitals=["BP: 170/102 mmHg"]
    )
    assert risks["cardiac_risk"].upper() == "VERY HIGH"
    assert risks["renal_failure_risk"].upper() == "VERY HIGH"
    assert risks["overall_risk_level"].upper() == "CRITICAL"
