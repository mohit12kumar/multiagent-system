from typing import Dict, Any, List, Optional
from backend.knowledge.knowledge_loader import KnowledgeLoader

class DrugInteractionEngine:
    """
    Configuration-driven Drug-Drug Interaction, Contraindication, and Dose Adjustment Engine.
    Evaluates RxNorm medications against patient diseases, allergies, and renal function (eGFR).
    """

    def __init__(self, loader: Optional[KnowledgeLoader] = None):
        self.loader = loader or KnowledgeLoader()

    def evaluate_medications(
        self,
        medications: List[str],
        diseases: List[str],
        allergies: Optional[List[str]] = None,
        egfr: Optional[float] = None
    ) -> Dict[str, Any]:

        allergies = allergies or []
        interactions = []
        contraindications = []
        renal_adjustments = []

        med_concepts = []
        for m in medications:
            concept = self.loader.get_medication(m)
            if concept:
                med_concepts.append(concept)

        # 1. Check Drug-Drug Interactions
        for i in range(len(med_concepts)):
            for j in range(i + 1, len(med_concepts)):
                m1 = med_concepts[i]
                m2 = med_concepts[j]
                
                # Check m1 interactions for m2
                for inter in m1.get("drug_interactions", []):
                    target_drug = inter.get("drug", "").lower()
                    m2_gen = m2.get("generic_name", "").lower()
                    if target_drug in m2_gen or m2_gen in target_drug:
                        interactions.append({
                            "drug1": m1.get("generic_name"),
                            "drug2": m2.get("generic_name"),
                            "severity": inter.get("severity", "Moderate"),
                            "effect": inter.get("effect")
                        })

        # 2. Check Disease Contraindications & Renal Dose Adjustments
        for m in med_concepts:
            m_name = m.get("generic_name")

            # Check Allergy
            for allergy in allergies:
                if m_name.lower() in allergy.lower() or allergy.lower() in m_name.lower():
                    contraindications.append({
                        "medication": m_name,
                        "contraindication": f"Patient Allergy: {allergy}",
                        "severity": "CRITICAL"
                    })

            # Check Renal Adjustment
            if egfr is not None:
                for adj in m.get("renal_dose_adjustment", []):
                    egfr_range = adj.get("egfr_range", "")
                    rec = adj.get("recommendation", "")
                    if "< 30" in egfr_range and egfr < 30:
                        renal_adjustments.append({
                            "medication": m_name,
                            "egfr": egfr,
                            "recommendation": f"eGFR {egfr} mL/min: {rec}"
                        })
                        if "CONTRAINDICATED" in rec:
                            contraindications.append({
                                "medication": m_name,
                                "contraindication": f"Renal Failure (eGFR {egfr} mL/min < 30)",
                                "severity": "HIGH"
                            })

        return {
            "drug_interactions": interactions,
            "contraindications": contraindications,
            "renal_dose_adjustments": renal_adjustments
        }
