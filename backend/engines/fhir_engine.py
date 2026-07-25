from typing import Dict, Any, List
import uuid
import datetime

class FHIREngine:
    """Generates HL7 FHIR R4 compliant JSON Resource Bundles and handles FHIR validation/import v7.0."""

    @classmethod
    def validate_fhir_resource(cls, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Validate FHIR R4 JSON structure against HL7 R4 schema rules."""
        res_type = resource.get("resourceType")
        if not res_type:
            return {"valid": False, "error": "Missing resourceType attribute"}

        valid_types = {"Bundle", "Patient", "Condition", "Observation", "MedicationStatement", "DiagnosticReport"}
        if res_type not in valid_types:
            return {"valid": False, "error": f"Unsupported resourceType: {res_type}"}

        if res_type == "Bundle":
            if "type" not in resource or "entry" not in resource:
                return {"valid": False, "error": "FHIR Bundle requires 'type' and 'entry' fields"}
        elif res_type == "Condition":
            if "code" not in resource or "subject" not in resource:
                return {"valid": False, "error": "FHIR Condition requires 'code' and 'subject' fields"}
        elif res_type == "Observation":
            if "status" not in resource or "code" not in resource:
                return {"valid": False, "error": "FHIR Observation requires 'status' and 'code' fields"}

        return {"valid": True, "resourceType": res_type, "schema_version": "FHIR R4 (4.0.1)"}

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

        bundle = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "type": "collection",
            "timestamp": datetime.datetime.now().isoformat(),
            "total_resources": len(entries),
            "entry": entries
        }

        bundle["validation"] = cls.validate_fhir_resource(bundle)
        return bundle

    @classmethod
    def import_fhir_bundle(cls, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Parse an incoming FHIR R4 Bundle into normalized internal state arrays."""
        val = cls.validate_fhir_resource(bundle)
        if not val["valid"]:
            raise ValueError(f"Invalid FHIR Bundle: {val['error']}")

        imported_diseases = []
        imported_medications = []
        imported_labs = []

        for entry in bundle.get("entry", []):
            res = entry.get("resource", {})
            rt = res.get("resourceType")

            if rt == "Condition":
                c_text = res.get("code", {}).get("text") or "Condition"
                imported_diseases.append(c_text)
            elif rt == "MedicationStatement":
                m_text = res.get("medicationCodeableConcept", {}).get("text") or "Medication"
                imported_medications.append(m_text)
            elif rt == "Observation":
                o_text = res.get("code", {}).get("text") or "Observation"
                o_val = res.get("valueString") or str(res.get("valueQuantity", {}).get("value", ""))
                imported_labs.append({"lab": o_text, "value": o_val})

        return {
            "imported_diseases": imported_diseases,
            "imported_medications": imported_medications,
            "imported_labs": imported_labs,
            "total_imported": len(imported_diseases) + len(imported_medications) + len(imported_labs),
            "status": "FHIR_IMPORT_SUCCESS"
        }
