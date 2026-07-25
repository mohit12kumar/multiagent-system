from typing import Dict, Any, List
import uuid
import datetime

class FHIREngine:
    """Generates HL7 FHIR R4 compliant JSON Resource Bundles."""

    @classmethod
    def build_fhir_bundle(
        cls,
        patient_id: str,
        diseases: List[Dict[str, Any]],
        medications: List[Dict[str, Any]],
        labs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        bundle_id = str(uuid.uuid4())
        entries = []

        # 1. Patient Resource
        entries.append({
            "fullUrl": f"urn:uuid:patient-{patient_id}",
            "resource": {
                "resourceType": "Patient",
                "id": patient_id,
                "active": True,
                "gender": "unknown"
            }
        })

        # 2. Condition Resources (Diseases)
        for d in diseases:
            d_name = d.get("name") if isinstance(d, dict) else str(d)
            icd10 = d.get("icd10", "I99.9") if isinstance(d, dict) else "I99.9"
            snomed = d.get("snomed", "404684003") if isinstance(d, dict) else "404684003"
            entries.append({
                "fullUrl": f"urn:uuid:condition-{uuid.uuid4()}",
                "resource": {
                    "resourceType": "Condition",
                    "clinicalStatus": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
                    },
                    "code": {
                        "coding": [
                            {"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": icd10, "display": d_name},
                            {"system": "http://snomed.info/sct", "code": snomed, "display": d_name}
                        ],
                        "text": d_name
                    },
                    "subject": {"reference": f"Patient/{patient_id}"}
                }
            })

        # 3. Observation Resources (Labs)
        for l in labs:
            l_name = l.get("lab") or l.get("name", "Lab") if isinstance(l, dict) else str(l)
            l_val = l.get("value", "") if isinstance(l, dict) else str(l)
            entries.append({
                "fullUrl": f"urn:uuid:observation-{uuid.uuid4()}",
                "resource": {
                    "resourceType": "Observation",
                    "status": "final",
                    "code": {"text": l_name},
                    "valueString": str(l_val),
                    "subject": {"reference": f"Patient/{patient_id}"}
                }
            })

        # 4. MedicationStatement Resources
        for m in medications:
            m_name = m.get("name", "Medication") if isinstance(m, dict) else str(m)
            entries.append({
                "fullUrl": f"urn:uuid:medicationstatement-{uuid.uuid4()}",
                "resource": {
                    "resourceType": "MedicationStatement",
                    "status": "active",
                    "medicationCodeableConcept": {"text": m_name},
                    "subject": {"reference": f"Patient/{patient_id}"}
                }
            })

        return {
            "resourceType": "Bundle",
            "id": bundle_id,
            "type": "collection",
            "timestamp": datetime.datetime.now().isoformat(),
            "total_resources": len(entries),
            "entry": entries
        }
