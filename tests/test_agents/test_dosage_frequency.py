import pytest
from src.agents.extraction.dosage_frequency_agent import DosageFrequencyAgent

def test_dosage_frequency_extraction():
    sentences = [
        {"text": "Prescribed Metformin 500mg once daily.", "start_char": 0, "end_char": 38}
    ]
    agent = DosageFrequencyAgent(config={})
    extractions = agent.extract(sentences)
    
    # Expect 1 dosage ("500mg") and 1 frequency ("once daily")
    assert len(extractions) == 2
    
    dosages = [e for e in extractions if e.type == "DOSAGE"]
    frequencies = [e for e in extractions if e.type == "FREQUENCY"]
    
    assert len(dosages) == 1
    assert dosages[0].text == "500mg"
    assert dosages[0].start_char == 21
    assert dosages[0].end_char == 26
    
    assert len(frequencies) == 1
    assert frequencies[0].text == "once daily"
    assert frequencies[0].start_char == 27
    assert frequencies[0].end_char == 37
