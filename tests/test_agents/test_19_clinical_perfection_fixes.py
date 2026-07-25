import pytest
from backend.models.pipeline_state import PipelineState
from backend.models.entity import EntityMentionModel
from backend.agents.formatting_agent import FormattingAgent
from backend.agents.lab_interpretation_agent import LabInterpretationAgent
from backend.clinical.clinical_context_classifier import ClinicalContextClassifier
from backend.clinical.clinical_knowledge_graph import ClinicalKnowledgeGraph
from backend.clinical.clinical_recommendation_engine import ClinicalRecommendationEngine

NOTE_TEXT = """
Patient Name: John Smith
Age: 67 years
Gender: Male

Assessment:
Acute Inferior STEMI
Acute Decompensated Heart Failure
Chronic Kidney Disease Stage III
Acute Kidney Injury
Hyperkalemia
Community Acquired Pneumonia
Type 2 Diabetes Mellitus
Hypertension
Hyperlipidemia

Vital Signs:
BP 168/102 mmHg
Heart Rate 118 bpm
Respiratory Rate 30/min
Temperature 39.2°C
SpO2 84%

Laboratory Results:
Troponin-I 8.6 ng/mL
BNP 2950 pg/mL
Creatinine 4.2 mg/dL
eGFR 15 mL/min
BUN 72 mg/dL
Potassium 6.8 mmol/L
HbA1c 9.4%
Blood Glucose 318 mg/dL
WBC 18,500/mm³
CRP 228 mg/L
LDL 210 mg/dL
HDL 28 mg/dL
Triglycerides 322 mg/dL

Imaging:
ECG: ST elevation in leads II, III and aVF.
Chest X-ray: Right lower lobe infiltrate.
Echocardiography: Ejection Fraction 25%.

Symptoms:
Chest pain
Shortness of breath
Sweating

Medications:
Aspirin 75 mg orally daily
Metformin 1000 mg orally twice daily
Atorvastatin 80 mg orally at night
Furosemide 40 mg IV twice daily
"""

def make_ent(text, ent_type):
    start = NOTE_TEXT.find(text)
    return EntityMentionModel(text=text, type=ent_type, start_char=start if start >= 0 else 0, end_char=(start + len(text)) if start >= 0 else len(text))

def test_temperature_deduplication_and_normalization():
    agent = LabInterpretationAgent()
    vitals = agent.interpret_vitals(NOTE_TEXT)
    temp_entries = [v for v in vitals if v["vital"] == "Temperature"]
    
    assert len(temp_entries) == 1
    assert temp_entries[0]["value"] == "39.2 °C"
    assert "Fever" in temp_entries[0]["interpretation"]

def test_symptom_isolation_sweating():
    graph = ClinicalKnowledgeGraph.build_graph(
        diseases=["Acute Inferior STEMI", "Hyperlipidemia", "Acute Kidney Injury", "Hyperkalemia"],
        symptoms=["chest pain", "sweating"],
        medications=[{"name": "Aspirin", "dosage": "75 mg"}]
    )
    nodes = graph["nodes"]
    
    stemi = next(n for n in nodes if "STEMI" in n["name"])
    hld = next(n for n in nodes if "Hyperlipidemia" in n["name"])
    aki = next(n for n in nodes if "Kidney Injury" in n["name"])
    hyperk = next(n for n in nodes if "Hyperkalemia" in n["name"])
    
    assert "sweating" in stemi["symptoms"]
    assert "sweating" not in hld["symptoms"]
    assert "sweating" not in aki["symptoms"]
    assert "sweating" not in hyperk["symptoms"]

def test_hyperlipidemia_lipid_panel_evidence():
    graph = ClinicalKnowledgeGraph.build_graph(
        diseases=["Hyperlipidemia"],
        symptoms=["sweating"],
        medications=[{"name": "Atorvastatin", "dosage": "80 mg"}],
        labs=[
            {"lab": "LDL", "value": "210", "unit": "mg/dL", "interpretation": "Elevated"},
            {"lab": "HDL", "value": "28", "unit": "mg/dL", "interpretation": "Low"},
            {"lab": "Triglycerides", "value": "322", "unit": "mg/dL", "interpretation": "Elevated"}
        ]
    )
    hld_node = graph["nodes"][0]
    hld_labs = [l["name"] for l in hld_node["supporting_labs"]]
    
    assert "LDL" in hld_labs
    assert "HDL" in hld_labs
    assert "Triglycerides" in hld_labs
    assert "sweating" not in hld_node["symptoms"]

def test_imaging_attributions_per_disease():
    graph = ClinicalKnowledgeGraph.build_graph(
        diseases=["Acute Inferior STEMI", "Heart Failure", "Community Acquired Pneumonia"],
        symptoms=["chest pain"],
        medications=[]
    )
    nodes = graph["nodes"]
    stemi = next(n for n in nodes if "STEMI" in n["name"])
    hf = next(n for n in nodes if "Heart Failure" in n["name"])
    pneu = next(n for n in nodes if "Pneumonia" in n["name"])
    
    stemi_img = [i["name"] for i in stemi["supporting_imaging"]]
    hf_img = [i["name"] for i in hf["supporting_imaging"]]
    pneu_img = [i["name"] for i in pneu["supporting_imaging"]]
    
    assert "ECG" in stemi_img
    assert "Echocardiography" in hf_img
    assert "Chest X-Ray" in hf_img
    assert "Chest X-Ray" in pneu_img

def test_prioritized_recommendations():
    recs = ClinicalRecommendationEngine.generate_recommendations("Acute Inferior STEMI")
    timeframes = [r["timeframe"] for r in recs]
    
    assert "Immediate" in timeframes
    assert "Within 1 Hour" in timeframes
    assert "Today" in timeframes
    assert any("PCI" in r["action"] for r in recs)
