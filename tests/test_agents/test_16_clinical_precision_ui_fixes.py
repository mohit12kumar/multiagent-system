import pytest
from backend.agents.formatting_agent import FormattingAgent
from backend.models.pipeline_state import PipelineState
from src.models.entity import EntityMentionModel

def test_medication_dosage_span_resolution_precision():
    text = "Patient taking Metformin 1000 mg daily for Diabetes. Also prescribed Clopidogrel for CAD."
    state = PipelineState(
        session_id="test_dosage_span",
        document_id="doc_dosage_span",
        text=text
    )
    state.final_entities = [
        EntityMentionModel(text="Metformin", type="DRUG", start_char=15, end_char=24),
        EntityMentionModel(text="1000 mg", type="DOSAGE", start_char=25, end_char=32),
        EntityMentionModel(text="Diabetes", type="DISEASE", start_char=43, end_char=51),
        EntityMentionModel(text="Clopidogrel", type="DRUG", start_char=71, end_char=82),
        EntityMentionModel(text="CAD", type="DISEASE", start_char=87, end_char=90)
    ]
    
    agent = FormattingAgent()
    res = agent.process(state)

    meds = res.get("medications", [])
    assert "Clopidogrel" in meds
    assert "Metformin" in meds

    kg_nodes = res.get("knowledge_graph", {}).get("nodes", [])
    for node in kg_nodes:
        for m in node.get("medications", []):
            if m["name"] == "Clopidogrel":
                assert m["dosage"] != "1000 mg"
                assert m["dosage"] in ["Not Specified", "Unspecified", "75 mg", "300 mg"]

def test_disease_card_payload_completeness():
    state = PipelineState(
        session_id="test_card_payload",
        document_id="doc_card_payload",
        text="2012 Hypertension, 2014 Diabetes. Troponin 8.4 ng/mL, Potassium 6.7 mmol/L, eGFR 16 mL/min. Aspirin, Metformin prescribed."
    )
    state.final_entities = [
        EntityMentionModel(text="Acute Inferior STEMI", type="DISEASE", start_char=0, end_char=20),
        EntityMentionModel(text="Aspirin", type="DRUG", start_char=21, end_char=28)
    ]
    agent = FormattingAgent()
    res = agent.process(state)

    diseases = res.get("diseases", [])
    assert len(diseases) > 0
    d = diseases[0]
    assert "disease" in d
    assert "icd10" in d
    assert "severity" in d
    assert "supporting_evidence" in d or "supporting_labs" in d
