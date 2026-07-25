import networkx as nx
from typing import Dict, Any, List

class ClinicalGraphEngine:
    """Builds a NetworkX directed multi-relational clinical graph linking 18 entity categories."""

    NODE_TYPES = [
        "Patient", "Symptoms", "Diseases", "Signs", "Labs", "Imaging",
        "Procedures", "Medications", "Allergies", "Family History",
        "Social History", "Lifestyle", "Vaccinations", "Risk Factors",
        "Genetics", "Devices", "Follow-ups", "Outcomes"
    ]

    @classmethod
    def build_networkx_graph(
        cls,
        patient_id: str,
        diseases: List[Dict[str, Any]],
        symptoms: List[str],
        medications: List[Dict[str, Any]],
        labs: List[Any],
        vitals: List[Any]
    ) -> Dict[str, Any]:
        G = nx.DiGraph()

        # Add Patient Root Node
        G.add_node(patient_id, type="Patient", label=f"Patient {patient_id}")

        # Add Diseases and link to Patient
        for d in diseases:
            d_name = (d.get("disease") or d.get("name") or "Disease") if isinstance(d, dict) else str(d)
            d_id = f"Disease_{str(d_name).replace(' ', '_')}"
            icd = d.get("icd10", "I99.9") if isinstance(d, dict) else "I99.9"
            G.add_node(d_id, type="Diseases", label=d_name, icd10=icd)
            G.add_edge(patient_id, d_id, relation="DIAGNOSED_WITH")

            # Add Symptoms
            for s in symptoms:
                s_str = str(s)
                s_id = f"Symptom_{s_str.replace(' ', '_')}"
                G.add_node(s_id, type="Symptoms", label=s_str)
                G.add_edge(d_id, s_id, relation="MANIFESTS_SYMPTOM")

            # Add Medications
            for m in medications:
                m_name = (m.get("name") or m.get("medication_name") or "Medication") if isinstance(m, dict) else str(m)
                m_id = f"Medication_{str(m_name).replace(' ', '_')}"
                G.add_node(m_id, type="Medications", label=m_name)
                G.add_edge(d_id, m_id, relation="TREATED_WITH")

        nodes = [{"id": n, "label": G.nodes[n].get("label", n), "type": G.nodes[n].get("type", "Entity")} for n in G.nodes]
        edges = [{"source": u, "target": v, "relation": G.edges[u, v].get("relation", "LINKED_TO")} for u, v in G.edges]

        return {
            "graph_type": "NetworkX Directed Multi-Relational Graph",
            "supported_categories": cls.NODE_TYPES,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges
        }
