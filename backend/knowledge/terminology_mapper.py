from typing import Dict, Any, List, Optional
from backend.knowledge.knowledge_loader import KnowledgeLoader

class TerminologyMapper:
    """
    Unified Terminology & Standard Code Mapper for open medical ontologies:
    - ICD-10-CM
    - ICD-11
    - LOINC
    - RxNorm
    - Disease Ontology (DOID)
    - Human Phenotype Ontology (HPO)
    - MeSH
    - FHIR R4 Resource Mapping
    """

    def __init__(self, loader: Optional[KnowledgeLoader] = None):
        self.loader = loader or KnowledgeLoader()

    def map_disease_concept(self, disease_name: str) -> Dict[str, Any]:
        concept = self.loader.get_disease(disease_name)
        if concept:
            return {
                "disease_name": concept.get("disease_name"),
                "icd10": concept.get("icd10", "Unspecified"),
                "icd11": concept.get("icd11", "Unspecified"),
                "ontology_id": concept.get("ontology_id", "DOID:Unknown"),
                "hpo_id": concept.get("hpo_id", "HP:Unknown"),
                "mesh_id": concept.get("mesh_id", "Unknown"),
                "fhir_mapping": concept.get("fhir_mapping", {})
            }
        return {
            "disease_name": disease_name,
            "icd10": "R69",
            "icd11": "MG90",
            "ontology_id": "DOID:4",
            "hpo_id": "HP:0000118",
            "mesh_id": "D004194",
            "fhir_mapping": {
                "resourceType": "Condition",
                "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "R69", "display": disease_name}]}
            }
        }

    def map_medication_concept(self, medication_name: str) -> Dict[str, Any]:
        concept = self.loader.get_medication(medication_name)
        if concept:
            return {
                "generic_name": concept.get("generic_name"),
                "rxnorm_code": concept.get("rxnorm_code", "Unknown"),
                "drug_class": concept.get("drug_class", "General Agent"),
                "brand_names": concept.get("brand_names", []),
                "fhir_mapping": concept.get("fhir_mapping", {})
            }
        return {
            "generic_name": medication_name.capitalize(),
            "rxnorm_code": "000000",
            "drug_class": "Therapeutic Agent",
            "brand_names": [],
            "fhir_mapping": {
                "resourceType": "Medication",
                "code": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "000000", "display": medication_name}]}
            }
        }

    def map_lab_concept(self, lab_name: str) -> Dict[str, Any]:
        concept = self.loader.get_lab(lab_name)
        if concept:
            return {
                "test_name": concept.get("test_name"),
                "loinc_code": concept.get("loinc_code", "Unknown"),
                "unit": concept.get("unit", ""),
                "reference_range": concept.get("reference_range", {})
            }
        return {
            "test_name": lab_name,
            "loinc_code": "99999-9",
            "unit": "unit",
            "reference_range": {}
        }
