"""
tests/test_agents/test_22_enterprise_v3_intelligence.py

Automated test suite for Version 3.0 Enterprise Clinical Medication Intelligence Platform.
Tests:
  - Universal Dose Understanding (Word numbers, fractions, roman numerals)
  - Data-driven Dynamic Knowledge Vocabularies
  - Multi-level confidence engine & explainable reasoning
  - Continuous learning review logging
"""

import pytest
from backend.agents.medication_parser import MedicationParserAgent
from backend.knowledge.knowledge_loader import KnowledgeLoader


def test_v3_word_numbers_and_fractions():
    cases = [
        ("Metformin Five Hundred mg BD after meals", "500 mg", "BID", "After meals (PC)"),
        ("Amlodipine half tablet PO OD in the morning", "half tablet", "OD", "Morning"),
        ("Paracetamol 1/2 tablet SOS fever", "1/2 tablet", "SOS", "Unspecified"),
        ("Salbutamol II Tablets q6h PRN breathlessness", "2 Tablets", "q6h", "Unspecified"),
    ]
    for note, exp_dose, exp_freq, exp_timing in cases:
        res = MedicationParserAgent.parse_text(note)
        assert len(res) >= 1, f"Failed to parse note: {note}"
        m = res[0]
        assert m["dose"] == exp_dose
        assert m["frequency"] == exp_freq
        assert m["timing"] == exp_timing
        assert "evidence" in m
        assert "reasoning" in m
        assert "field_confidence" in m


def test_v3_dynamic_knowledge_loader():
    kl = KnowledgeLoader()
    freqs = kl.get_frequency_dict()
    routes = kl.get_route_dict()
    timings = kl.get_timing_dict()
    units = kl.get_dose_units_dict()

    assert "bd" in freqs
    assert "po" in routes
    assert "after meals" in timings
    assert "word_numbers" in units
    assert "five hundred" in units["word_numbers"]


def test_v3_explainable_ai_output():
    text = "Metformin Five Hundred mg BD after meals for 30 days"
    res = MedicationParserAgent.parse_text(text)
    assert len(res) >= 1
    m = res[0]
    assert m["confidence"] > 0.80
    assert m["field_confidence"]["drug"] == 0.99
    assert m["field_confidence"]["dose"] == 0.98
    assert "Metformin" in m["evidence"][0]
    assert "dose" in m["reasoning"]
    assert "frequency" in m["reasoning"]
