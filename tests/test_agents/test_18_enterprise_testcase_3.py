import pytest
from backend.models.pipeline_state import PipelineState
from backend.models.entity import EntityMentionModel
from backend.agents.formatting_agent import FormattingAgent
from backend.clinical.clinical_context_classifier import ClinicalContextClassifier
from backend.clinical.clinical_knowledge_graph import ClinicalKnowledgeGraph

NOTE_TEXT = """
Patient Name: John Smith
Age: 67 years
Gender: Male

Chief Complaint:
Severe central chest pain radiating to the left arm for 2 hours with sweating and shortness of breath.

History of Present Illness:
The patient has a history of hypertension diagnosed in 2012, Type 2 Diabetes Mellitus diagnosed in 2015, Coronary Artery Disease with PCI performed in 2019, and Chronic Kidney Disease Stage III diagnosed in 2022.

The patient denies fever.
The patient denies cough.
The patient denies abdominal pain.

Past Medical History:
Hypertension
Type 2 Diabetes Mellitus
Coronary Artery Disease
CKD Stage III

Family History:
Father had Type 2 Diabetes Mellitus.
Mother had Hypertension.
Brother had stroke at age 58.

Social History:
Smokes one pack per day for 40 years.
Occasional alcohol use.

Allergies:
Penicillin allergy causing skin rash.

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
Chest X-ray: Pulmonary edema with right lower lobe infiltrate.
Echocardiography: Ejection Fraction 25%.

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

Medications:
Aspirin 75 mg orally once daily
Clopidogrel 300 mg loading dose orally
Atorvastatin 80 mg orally at night
Furosemide 40 mg IV twice daily
Metformin 1000 mg orally twice daily
Losartan 100 mg orally once daily
Insulin Glargine 20 units subcutaneous nightly
Ceftriaxone 1 g IV daily
Azithromycin 500 mg orally daily
Omeprazole 20 mg orally daily
"""

def make_ent(text, ent_type, find_str=None):
    search = find_str or text
    start = NOTE_TEXT.find(search)
    return EntityMentionModel(text=text, type=ent_type, start_char=start, end_char=start + len(text))

def test_enterprise_testcase_3_end_to_end():
    state = PipelineState(session_id="test_case_3", document_id="doc_test_3", text=NOTE_TEXT)

    # Entities mocking realistic multi-agent NER extraction
    state.final_entities = [
        make_ent("Acute Inferior STEMI", "DISEASE", "Assessment:\nAcute Inferior STEMI"),
        make_ent("Acute Decompensated Heart Failure", "DISEASE"),
        make_ent("Chronic Kidney Disease Stage III", "DISEASE", "Assessment:\nAcute Inferior STEMI\nAcute Decompensated Heart Failure\nChronic Kidney Disease Stage III"),
        make_ent("Acute Kidney Injury", "DISEASE"),
        make_ent("Hyperkalemia", "DISEASE"),
        make_ent("Community Acquired Pneumonia", "DISEASE"),
        make_ent("Type 2 Diabetes Mellitus", "DISEASE", "Assessment:\nAcute Inferior STEMI\nAcute Decompensated Heart Failure\nChronic Kidney Disease Stage III\nAcute Kidney Injury\nHyperkalemia\nCommunity Acquired Pneumonia\nType 2 Diabetes Mellitus"),
        make_ent("Hypertension", "DISEASE", "Assessment:\nAcute Inferior STEMI\nAcute Decompensated Heart Failure\nChronic Kidney Disease Stage III\nAcute Kidney Injury\nHyperkalemia\nCommunity Acquired Pneumonia\nType 2 Diabetes Mellitus\nHypertension"),
        make_ent("Hyperlipidemia", "DISEASE"),
        make_ent("Coronary Artery Disease", "DISEASE"),

        # Symptoms (Active & Negated)
        make_ent("chest pain", "SYMPTOM"),
        make_ent("shortness of breath", "SYMPTOM"),
        make_ent("fever", "SYMPTOM"),
        make_ent("cough", "SYMPTOM"),

        # Family History entities
        make_ent("stroke", "DISEASE"),

        # Allergy entity
        make_ent("Penicillin", "DRUG"),

        # Drugs
        make_ent("Aspirin", "DRUG", "Aspirin 75 mg"),
        make_ent("75 mg", "DOSAGE", "75 mg"),
        make_ent("Clopidogrel", "DRUG", "Clopidogrel 300 mg"),
        make_ent("300 mg", "DOSAGE", "300 mg"),
        make_ent("Furosemide", "DRUG", "Furosemide 40 mg"),
        make_ent("40 mg", "DOSAGE", "40 mg"),
        make_ent("Metformin", "DRUG", "Metformin 1000 mg"),
        make_ent("1000 mg", "DOSAGE", "1000 mg"),
        make_ent("Losartan", "DRUG", "Losartan 100 mg"),
        make_ent("100 mg", "DOSAGE", "100 mg"),
        make_ent("Ceftriaxone", "DRUG", "Ceftriaxone 1 g"),
        make_ent("1 g", "DOSAGE", "1 g"),
        make_ent("Azithromycin", "DRUG", "Azithromycin 500 mg"),
        make_ent("500 mg", "DOSAGE", "500 mg"),
        make_ent("Omeprazole", "DRUG", "Omeprazole 20 mg"),
        make_ent("20 mg", "DOSAGE", "20 mg"),

        # Labs
        make_ent("Troponin-I", "LAB_VALUE", "Troponin-I"),
        make_ent("BNP", "LAB_VALUE", "BNP 2950"),
        make_ent("Creatinine", "LAB_VALUE", "Creatinine 4.2"),
        make_ent("eGFR", "LAB_VALUE", "eGFR 15"),
        make_ent("HbA1c", "LAB_VALUE", "HbA1c 9.4%"),
        make_ent("LDL", "LAB_VALUE", "LDL 210")
    ]

    agent = FormattingAgent()
    res = agent.process(state)

    # 1. Negation & Family History Assertions
    context_res = ClinicalContextClassifier.filter_active_entities(NOTE_TEXT, state.final_entities)
    negated = [e.text for e in context_res["negated"]]
    family = [e.text for e in context_res["family_history"]]

    assert "fever" in negated
    assert "cough" in negated
    assert "stroke" in family
    assert "Penicillin" in context_res["allergies"]

    # 2. Disease Extraction Assertions
    kg_nodes = res.get("knowledge_graph", {}).get("nodes", [])
    node_names = [n["name"] for n in kg_nodes]

    assert any("STEMI" in n for n in node_names)
    assert any("Kidney Disease" in n for n in node_names)
    assert any("Diabetes" in n for n in node_names)
    assert any("Hypertension" in n for n in node_names)

    # 3. Dynamic Lab Attribution Assertions
    stemi_node = next(n for n in kg_nodes if "STEMI" in n["name"])
    ckd_node = next(n for n in kg_nodes if "Kidney Disease" in n["name"])
    dm_node = next(n for n in kg_nodes if "Diabetes" in n["name"])

    stemi_labs = [l["name"] for l in stemi_node["supporting_labs"]]
    ckd_labs = [l["name"] for l in ckd_node["supporting_labs"]]
    dm_labs = [l["name"] for l in dm_node["supporting_labs"]]

    assert any("troponin" in l.lower() for l in stemi_labs)
    assert not any("hba1c" in l.lower() for l in stemi_labs)
    assert any("creatinine" in l.lower() or "egfr" in l.lower() for l in ckd_labs)
    assert not any("troponin" in l.lower() for l in ckd_labs)
    assert any("hba1c" in l.lower() for l in dm_labs)
    assert not any("troponin" in l.lower() for l in dm_labs)

    # 4. Medication Dose & Route Resolution
    med_list = res.get("medications", [])
    assert "Aspirin" in med_list
    assert "Metformin" in med_list

    # 5. CKD Stage Discrepancy Assertion
    assert ckd_node["documented_stage"] == "CKD Stage III"
    assert "Stage IV" in ckd_node["inferred_stage"]
    assert ckd_node["staging_status"] == "Documentation Discrepancy Flagged"
