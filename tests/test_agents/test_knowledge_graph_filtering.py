import pytest
from backend.clinical.clinical_knowledge_graph import ClinicalKnowledgeGraph
from backend.clinical.medical_coder import MedicalCoder

def test_disease_specific_filtering():
    diseases = ["Hypertension", "Type 2 Diabetes Mellitus"]
    symptoms = [
        {"name": "dizziness", "disease_name": "Hypertension"},
        {"name": "frequent urination", "disease_name": "Type 2 Diabetes Mellitus"}
    ]
    medications = [
        {"name": "Amlodipine", "disease_name": "Hypertension", "dosage": "5mg"},
        {"name": "Metformin", "disease_name": "Type 2 Diabetes Mellitus", "dosage": "500mg"}
    ]
    
    graph = ClinicalKnowledgeGraph.build_graph(diseases, symptoms, medications)
    
    htn_node = next(n for n in graph["nodes"] if n["name"] == "Hypertension")
    dm_node = next(n for n in graph["nodes"] if n["name"] == "Type 2 Diabetes Mellitus")
    
    # Check that Hypertension only has Amlodipine and dizziness
    htn_med_names = [m["name"] for m in htn_node["medications"]]
    assert htn_med_names == ["Amlodipine"]
    assert htn_node["symptoms"] == ["dizziness"]
    
    # Check that Diabetes only has Metformin, and gets frequent urination (plus shared dizziness)
    dm_med_names = [m["name"] for m in dm_node["medications"]]
    assert dm_med_names == ["Metformin"]
    assert "frequent urination" in dm_node["symptoms"]

def test_medical_coder_word_boundary():
    # Hyperlipidemia should NOT match 'mi' (Myocardial Infarction)
    code_info = MedicalCoder.get_disease_codes("Hyperlipidemia")
    assert code_info["icd10"] == "E78.5"
    assert "Myocardial" not in code_info["official_name"]

    # Chronic Obstructive Pulmonary Disease should match J44.9
    copd_info = MedicalCoder.get_disease_codes("Chronic Obstructive Pulmonary Disease")
    assert copd_info["icd10"] == "J44.9"
