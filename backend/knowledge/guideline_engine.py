from typing import Dict, Any, List, Optional
from backend.knowledge.knowledge_loader import KnowledgeLoader

class GuidelineEngine:
    """
    Configuration-Driven Evidence & Clinical Practice Guideline Engine.
    Dynamically generates evidence attributions, investigation recommendations, and medication recommendations
    from ADA, KDIGO, GINA, GOLD, NICE, and CDC clinical guidelines.
    """

    def __init__(self, loader: Optional[KnowledgeLoader] = None):
        self.loader = loader or KnowledgeLoader()

    def generate_recommendations(self, diseases: List[str], eGFR: Optional[float] = None) -> Dict[str, Any]:
        attributions = []
        investigation_recs = []
        medication_recs = []

        for dis_name in diseases:
            concept = self.loader.get_disease(dis_name)
            if concept:
                for rec in concept.get("clinical_recommendations", []):
                    medication_recs.append(f"{concept.get('disease_name')}: {rec}")

                for gl in concept.get("guideline_references", []):
                    attributions.append({
                        "disease": concept.get("disease_name"),
                        "organization": gl.get("organization"),
                        "title": gl.get("title"),
                        "url": gl.get("url")
                    })

                for mon in concept.get("monitoring", []):
                    investigation_recs.append(f"{concept.get('disease_name')} Monitoring: {mon}")

        # Check eGFR Renal Guideline Rule if provided
        if eGFR is not None and eGFR < 30:
            for gl in self.loader.get_all_guidelines():
                if gl.get("id") == "GL-KDIGO-2024":
                    medication_recs.append("KDIGO 2024 Alert: eGFR < 30 mL/min/1.73m² — Discontinue Metformin and initiate nephrology referral for renal replacement modality planning.")

        return {
            "guideline_attributions": attributions,
            "guideline_investigation_recommendations": list(set(investigation_recs)),
            "guideline_medication_recommendations": list(set(medication_recs))
        }
