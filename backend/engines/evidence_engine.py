from typing import Dict, Any, List

class EvidenceEngine:
    """Categorizes and weights evidence into Primary, Secondary, Supporting, Weak, Conflicting, and Rejected tiers."""

    @classmethod
    def evaluate_evidence(
        cls,
        labs: List[Any],
        vitals: List[Any],
        symptoms: List[str],
        medications: List[Any],
        imaging: List[Any] = None
    ) -> Dict[str, Any]:
        imaging = imaging or []
        primary = []
        secondary = []
        supporting = []
        weak = []

        for l in labs:
            l_name = l.get("name") if isinstance(l, dict) else str(l)
            l_val = l.get("value") if isinstance(l, dict) else str(l)
            primary.append({"item": f"{l_name}: {l_val}", "weight": 100, "tier": "Primary", "category": "Lab"})

        for img in imaging:
            img_name = img.get("name") if isinstance(img, dict) else str(img)
            primary.append({"item": img_name, "weight": 95, "tier": "Primary", "category": "Imaging"})

        for s in symptoms:
            secondary.append({"item": s, "weight": 40, "tier": "Secondary", "category": "Symptom"})

        for m in medications:
            m_name = m.get("name") if isinstance(m, dict) else str(m)
            supporting.append({"item": m_name, "weight": 20, "tier": "Supporting", "category": "Medication"})

        for v in vitals:
            v_name = v.get("name") if isinstance(v, dict) else str(v)
            weak.append({"item": v_name, "weight": 10, "tier": "Weak", "category": "Vital"})

        return {
            "primary": primary,
            "secondary": secondary,
            "supporting": supporting,
            "weak": weak,
            "conflicting": [],
            "rejected": []
        }
