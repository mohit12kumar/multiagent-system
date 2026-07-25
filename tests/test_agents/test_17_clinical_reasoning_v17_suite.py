import pytest
from backend.clinical.clinical_context_classifier import ClinicalContextClassifier
from backend.engines.unit_normalization_engine import UnitNormalizationEngine
from backend.clinical.clinical_knowledge_graph import ClinicalKnowledgeGraph

class EntityMock:
    def __init__(self, text, ent_type, start_char=0):
        self.text = text
        self.type = ent_type
        self.start_char = start_char

def test_negation_and_context_classification():
    text = "Patient denies shortness of breath. No chest pain. Father had diabetes. History of CAD in 2018. Allergic to Penicillin. Presenting with severe hypertension."
    entities = [
        EntityMock("shortness of breath", "SYMPTOM", text.find("shortness of breath")),
        EntityMock("chest pain", "SYMPTOM", text.find("chest pain")),
        EntityMock("diabetes", "DISEASE", text.find("diabetes")),
        EntityMock("CAD", "DISEASE", text.find("CAD")),
        EntityMock("Penicillin", "DRUG", text.find("Penicillin")),
        EntityMock("hypertension", "DISEASE", text.find("hypertension"))
    ]

    res = ClinicalContextClassifier.filter_active_entities(text, entities)

    active_texts = [e.text for e in res["active"]]
    negated_texts = [e.text for e in res["negated"]]
    past_texts = [e.text for e in res["past_history"]]
    family_texts = [e.text for e in res["family_history"]]

    assert "hypertension" in active_texts
    assert "chest pain" in negated_texts or "shortness of breath" in negated_texts
    assert "CAD" in past_texts
    assert "diabetes" in family_texts
    assert "Penicillin" in res["allergies"]

def test_temperature_unit_normalization():
    parsed_c = UnitNormalizationEngine.parse_temperature("39.2", "C")
    assert parsed_c["status"] == "Fever (Hyperthermia)"

    parsed_f = UnitNormalizationEngine.parse_temperature("39.2", "F")
    assert parsed_f["is_implausible"] is True
    assert "Implausible Value" in parsed_f["status"]

def test_disease_specific_lab_isolation():
    diseases = ["Diabetes Mellitus", "Acute Inferior STEMI", "Chronic Kidney Disease"]
    symptoms = ["chest pain", "edema", "polyuria"]
    medications = [
        {"name": "Metformin", "disease_name": "Diabetes Mellitus"},
        {"name": "Aspirin", "disease_name": "Acute Inferior STEMI"}
    ]
    labs = [
        {"lab": "Troponin", "value": "8.6", "unit": "ng/mL", "interpretation": "Critical High"},
        {"lab": "HbA1c", "value": "10.4", "unit": "%", "interpretation": "High"},
        {"lab": "Creatinine", "value": "4.2", "unit": "mg/dL", "interpretation": "High"}
    ]

    graph = ClinicalKnowledgeGraph.build_graph(diseases, symptoms, medications, labs=labs)

    dm_node = next(n for n in graph["nodes"] if n["name"] == "Diabetes Mellitus")
    stemi_node = next(n for n in graph["nodes"] if n["name"] == "Acute Inferior STEMI")
    ckd_node = next(n for n in graph["nodes"] if n["name"] == "Chronic Kidney Disease")

    dm_lab_names = [l["name"] for l in dm_node["supporting_labs"]]
    stemi_lab_names = [l["name"] for l in stemi_node["supporting_labs"]]
    ckd_lab_names = [l["name"] for l in ckd_node["supporting_labs"]]

    # Verify lab isolation
    assert "HbA1c" in dm_lab_names
    assert "Troponin" not in dm_lab_names

    assert "Troponin" in stemi_lab_names
    assert "HbA1c" not in stemi_lab_names

    assert "Creatinine" in ckd_lab_names
    assert "Troponin" not in ckd_lab_names

def test_documented_vs_inferred_ckd_staging():
    diseases = ["Chronic Kidney Disease Stage III"]
    symptoms = ["edema"]
    medications = []
    labs = [{"lab": "eGFR", "value": "16", "unit": "mL/min", "interpretation": "Low"}]

    graph = ClinicalKnowledgeGraph.build_graph(diseases, symptoms, medications, labs=labs)
    ckd_node = graph["nodes"][0]

    assert ckd_node["documented_stage"] == "CKD Stage III"
    assert "Stage IV" in ckd_node["inferred_stage"]
    assert ckd_node["staging_status"] == "Documentation Discrepancy Flagged"
