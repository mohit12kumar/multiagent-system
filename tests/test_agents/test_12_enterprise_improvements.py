import pytest
from backend.clinical.clinical_knowledge_graph import ClinicalKnowledgeGraph
from backend.agents.contraindication_agent import ContraindicationAgent
from backend.clinical.severity_risk_engine import SeverityRiskEngine
from backend.agents.formatting_agent import FormattingAgent
from backend.models.pipeline_state import PipelineState
from src.models.entity import EntityMentionModel

def test_12_enterprise_improvements_knowledge_graph():
    diseases = [
        "Hyperlipidemia", "Heart Failure", "Acute Kidney Injury", 
        "Hyperkalemia", "COPD", "Community Acquired Pneumonia", "Acute Inferior STEMI"
    ]
    symptoms = ["Chest pain", "Shortness of breath", "Fever", "Wheezing"]
    medications = [
        {"name": "Atorvastatin", "dosage": "40 mg", "frequency": "daily", "route": "Oral"},
        {"name": "Furosemide", "dosage": "40 mg", "frequency": "BID", "route": "Oral"},
        {"name": "Aspirin", "dosage": "75 mg", "frequency": "daily", "route": "Oral"},
        {"name": "Clopidogrel", "dosage": "75 mg", "frequency": "daily", "route": "Oral"},
        {"name": "Losartan", "dosage": "50 mg", "frequency": "daily", "route": "Oral"},
        {"name": "Metformin", "dosage": "1000 mg", "frequency": "BID", "route": "Oral"}
    ]
    
    graph = ClinicalKnowledgeGraph.build_graph(diseases, symptoms, medications)
    nodes = {n["name"]: n for n in graph["nodes"]}
    
    # 1. Hyperlipidemia Card Evidence & Explainability
    assert "Hyperlipidemia" in nodes
    h_node = nodes["Hyperlipidemia"]
    assert "supporting_evidence" in h_node
    assert len(h_node["detected_because"]) >= 2
    
    # 2. Heart Failure Card
    assert "Heart Failure" in nodes
    hf_node = nodes["Heart Failure"]
    assert "supporting_evidence" in hf_node
    assert len(hf_node["detected_because"]) >= 2
    
    # 3. AKI Card
    assert "Acute Kidney Injury" in nodes
    aki_node = nodes["Acute Kidney Injury"]
    assert "supporting_evidence" in aki_node
    assert len(aki_node["detected_because"]) >= 2
    
    # 4. Hyperkalemia
    assert "Hyperkalemia" in nodes
    hk_node = nodes["Hyperkalemia"]
    assert "supporting_evidence" in hk_node
    assert len(hk_node["detected_because"]) >= 2
    
    # 5. COPD
    assert "COPD" in nodes
    copd_node = nodes["COPD"]
    assert "supporting_evidence" in copd_node
    
    # 6. Pneumonia
    assert "Community Acquired Pneumonia" in nodes
    pneu_node = nodes["Community Acquired Pneumonia"]
    assert "supporting_evidence" in pneu_node

def test_12_enterprise_improvements_contraindications():
    agent = ContraindicationAgent()
    
    # 8. Contraindications (Metformin + eGFR/CKD/AKI, Losartan + Hyperkalemia, DAPT, Duplicate Statins)
    meds = ["Metformin 1000 mg", "Losartan 50 mg", "Aspirin 75 mg", "Clopidogrel 75 mg", "Atorvastatin 40 mg", "Rosuvastatin 20 mg"]
    diseases = ["Chronic Kidney Disease", "Hyperkalemia", "Acute Inferior STEMI"]
    allergies = ["NKDA"]
    
    warnings = agent.check_contraindications(meds, diseases, allergies)
    w_text = " ".join([w["warning"] for w in warnings])
    
    assert "Metformin" in w_text
    assert "Losartan" in w_text
    assert "Dual Antiplatelet Therapy" in w_text
    assert "Duplicate statin therapy" in w_text

    # Verify structured fields
    for w in warnings:
        assert "drug" in w
        assert "severity" in w
        assert "reason" in w
        assert "risk" in w
        assert "recommendation" in w

def test_12_enterprise_improvements_organ_risk_and_formatting():
    # 9. Organ Risk Assessment
    organ_risk = SeverityRiskEngine.compute_organ_risk_stratification(
        diseases=["Acute Inferior STEMI", "Heart Failure", "Chronic Kidney Disease", "Hyperkalemia"],
        labs=["Creatinine 4.1", "eGFR 16", "Potassium 6.7", "Troponin 8.4", "BNP 2800"],
        vitals=["SpO2 82%"]
    )
    assert organ_risk["cardiac"] == "VERY HIGH"
    assert organ_risk["renal"] == "VERY HIGH"
    assert organ_risk["overall"] == "CRITICAL"

    # 7, 10, 11, 12. Formatting Agent (Checklist, Explainability, Timeline, Missing Info)
    state = PipelineState(
        session_id="test_sess",
        document_id="test_doc",
        text="Patient with 2012 Hypertension, 2014 Diabetes, 2018 CAD, 2021 CKD. Presenting today with Acute Inferior STEMI, Heart Failure, AKI, Hyperkalemia."
    )
    state.final_entities = [
        EntityMentionModel(text="Acute Inferior STEMI", type="DISEASE", start_char=0, end_char=20),
        EntityMentionModel(text="Aspirin", type="DRUG", start_char=21, end_char=28)
    ]
    agent = FormattingAgent()
    res = agent.process(state)
    
    assert "medication_validation" in res
    assert res["medication_validation"]["score"] == 90
    assert res["medication_validation"]["duration"] == False
    
    assert "organ_risk" in res
    assert res["organ_risk"]["overall"] == "CRITICAL"

    assert "missing_information" in res
    assert "history" in res["missing_information"]
    assert "labs" in res["missing_information"]
    assert "vitals" in res["missing_information"]
    
    assert "timeline" in res
    assert len(res["timeline"]) >= 3
    assert any(t.get("date") == "2012" or t.get("year") == "2012" for t in res["timeline"])

