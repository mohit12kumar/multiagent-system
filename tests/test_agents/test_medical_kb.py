import pytest
from src.medical_kb.rxnorm_client import RxNormClient
from src.medical_kb.snomed_client import SnomedClient
from src.medical_kb.umls_client import UmlsClient

def test_rxnorm_client_resolution():
    client = RxNormClient()
    # Metformin is mapped to 6809 in data/gazetteers/drug_list.csv
    rxcui = client.get_rxcui("Metformin")
    assert rxcui == "6809"

def test_snomed_client_resolution():
    client = SnomedClient()
    # Hypertension is mapped to 38341003 in data/gazetteers/disease_list.csv
    code = client.get_snomed_code("Hypertension")
    assert code == "38341003"

def test_umls_client_resolution():
    client = UmlsClient()
    # Heart is mapped to C0018787 in data/gazetteers/anatomy_terms.csv
    cui = client.get_cui("Heart")
    assert cui == "C0018787"
