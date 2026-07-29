from typing import Dict, Any, List, Optional
from backend.knowledge.knowledge_loader import KnowledgeLoader

class KnowledgeSearchEngine:
    """
    Search & Retrieval Engine across configuration-driven medical concepts.
    Allows searching thousands of diseases, medications, and lab tests by query text, ICD code, or findings.
    """

    def __init__(self, loader: Optional[KnowledgeLoader] = None):
        self.loader = loader or KnowledgeLoader()

    def search_diseases(self, query: str) -> List[Dict[str, Any]]:
        q_low = query.strip().lower()
        results = []
        for dis in self.loader.get_all_diseases():
            dis_name = dis.get("disease_name", "").lower()
            icd10 = dis.get("icd10", "").lower()
            icd11 = dis.get("icd11", "").lower()
            symptoms = [s.lower() for s in dis.get("symptoms", [])]
            
            if q_low in dis_name or q_low in icd10 or q_low in icd11 or any(q_low in sym for sym in symptoms):
                results.append(dis)
        return results

    def search_medications(self, query: str) -> List[Dict[str, Any]]:
        q_low = query.strip().lower()
        results = []
        for med in self.loader.get_all_medications():
            gen_name = med.get("generic_name", "").lower()
            brand_names = [b.lower() for b in med.get("brand_names", [])]
            rxnorm = med.get("rxnorm_code", "").lower()
            drug_class = med.get("drug_class", "").lower()

            if q_low in gen_name or q_low in rxnorm or q_low in drug_class or any(q_low in b for b in brand_names):
                results.append(med)
        return results

    def search_labs(self, query: str) -> List[Dict[str, Any]]:
        q_low = query.strip().lower()
        results = []
        for lab in self.loader.get_all_labs():
            test_name = lab.get("test_name", "").lower()
            canon_name = lab.get("canonical_name", "").lower()
            loinc = lab.get("loinc_code", "").lower()

            if q_low in test_name or q_low in canon_name or q_low in loinc:
                results.append(lab)
        return results
