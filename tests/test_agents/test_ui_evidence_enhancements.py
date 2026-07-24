import pytest
from backend.clinical.clinical_knowledge_graph import ClinicalKnowledgeGraph
from backend.clinical.severity_risk_engine import SeverityRiskEngine

def test_hyperlipidemia_statin_and_lab_linking():
    diseases = ["Hyperlipidemia"]
    symptoms = []
    meds = [{"name": "Atorvastatin 20 mg", "dosage": "20 mg", "frequency": "Once Daily"}]
    labs = [{"lab": "LDL", "value": "172", "arrow": "↑", "supporting_disease": "Hyperlipidemia"}]

    kg = ClinicalKnowledgeGraph.build_graph(diseases, symptoms, meds, [], labs)
    node = kg["nodes"][0]
    assert node["name"] == "Hyperlipidemia"
    assert len(node["medications"]) >= 1
    assert "Atorvastatin" in node["medications"][0]["name"]

def test_enhanced_severity_label_generation():
    sev_htn, r_htn = SeverityRiskEngine.evaluate_severity("Hypertension", ["headache"], ["BP: 150/95"], [])
    assert "Stage 2" in sev_htn

    sev_db, r_db = SeverityRiskEngine.evaluate_severity("Type 2 Diabetes", [], [], [{"lab": "HbA1c", "value": "8.5"}])
    assert "Poor Glycemic Control" in sev_db

    sev_hl, r_hl = SeverityRiskEngine.evaluate_severity("Hyperlipidemia", [], [], [])
    assert "Severe Dyslipidemia" in sev_hl or "High CV Risk" in sev_hl
