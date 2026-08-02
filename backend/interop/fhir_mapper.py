"""
backend/interop/fhir_mapper.py

FHIR R4 Bundle Generator & Schema Validation Engine.
Converts clinical extraction payloads into official HL7 FHIR R4 Collection/Transaction Bundles.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class FHIRValidationError(Exception):
    """Raised when generated FHIR resources violate FHIR R4 structural schema rules."""
    pass


class FHIRMapper:
    """
    HL7 FHIR R4 Resource Converter and Bundle Builder.
    """

    FHIR_VERSION = "4.0.1"

    def build_patient_resource(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maps patient demographics to FHIR R4 Patient resource."""
        patient_id = patient_data.get("id") or str(uuid.uuid4())
        gender = str(patient_data.get("gender", "unknown")).lower()
        if gender not in ["male", "female", "other", "unknown"]:
            gender = "unknown"

        resource = {
            "resourceType": "Patient",
            "id": patient_id,
            "gender": gender,
        }

        if "name" in patient_data:
            resource["name"] = [{"text": patient_data["name"]}]
        if "birthDate" in patient_data or "dob" in patient_data:
            resource["birthDate"] = patient_data.get("birthDate") or patient_data.get("dob")
        if "age" in patient_data:
            resource["extension"] = [{
                "url": "http://hl7.org/fhir/StructureDefinition/patient-age",
                "valueInteger": int(patient_data["age"])
            }]

        return resource

    def build_condition_resource(self, condition_data: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """Maps clinical diagnosis / problem to FHIR R4 Condition resource."""
        cond_id = condition_data.get("id") or str(uuid.uuid4())
        name = condition_data.get("name") or condition_data.get("disease_name") or "Unspecified Condition"
        icd10 = condition_data.get("icd10")

        coding = [{"system": "http://snomed.info/sct", "display": name}]
        if icd10:
            coding.append({"system": "http://hl7.org/fhir/sid/icd-10", "code": icd10, "display": name})

        return {
            "resourceType": "Condition",
            "id": cond_id,
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active"
                }]
            },
            "code": {"coding": coding, "text": name},
            "subject": {"reference": f"Patient/{patient_id}"}
        }

    def build_medication_request_resource(self, med_data: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """Maps medication extraction to FHIR R4 MedicationRequest resource."""
        req_id = med_data.get("id") or str(uuid.uuid4())
        med_name = med_data.get("name") or med_data.get("generic_name") or "Unspecified Medication"
        rxnorm = med_data.get("rxnorm_code")

        coding = [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "display": med_name}]
        if rxnorm:
            coding[0]["code"] = str(rxnorm)

        dosage_instruction = {}
        if "dose" in med_data or "frequency" in med_data:
            dosage_text = f"{med_data.get('dose', '')} {med_data.get('route', '')} {med_data.get('frequency', '')}".strip()
            dosage_instruction = {"text": dosage_text}
            if "route" in med_data:
                dosage_instruction["route"] = {"text": med_data["route"]}

        res = {
            "resourceType": "MedicationRequest",
            "id": req_id,
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": coding,
                "text": med_name
            },
            "subject": {"reference": f"Patient/{patient_id}"}
        }
        if dosage_instruction:
            res["dosageInstruction"] = [dosage_instruction]

        return res

    def build_observation_resource(self, lab_data: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """Maps laboratory/vital test to FHIR R4 Observation resource."""
        obs_id = lab_data.get("id") or str(uuid.uuid4())
        test_name = lab_data.get("test_name") or lab_data.get("canonical_name") or "Laboratory Test"
        loinc = lab_data.get("loinc_code")

        coding = [{"system": "http://loinc.org", "display": test_name}]
        if loinc:
            coding[0]["code"] = str(loinc)

        res = {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final",
            "code": {"coding": coding, "text": test_name},
            "subject": {"reference": f"Patient/{patient_id}"}
        }

        if "val" in lab_data or "value" in lab_data:
            val = lab_data.get("val") if "val" in lab_data else lab_data.get("value")
            unit = lab_data.get("unit", "")
            try:
                num_val = float(val)
                res["valueQuantity"] = {
                    "value": num_val,
                    "unit": unit,
                    "system": "http://unitsofmeasure.org"
                }
            except (ValueError, TypeError):
                res["valueString"] = str(val)

        return res

    def create_bundle(
        self,
        extracted_data: Dict[str, Any],
        bundle_type: str = "collection"
    ) -> Dict[str, Any]:
        """
        Assembles all extracted entities into an HL7 FHIR R4 Bundle.
        """
        patient_info = extracted_data.get("patient") or extracted_data.get("demographics") or {"id": "patient-001"}
        patient_resource = self.build_patient_resource(patient_info)
        patient_id = patient_resource["id"]

        entries = [
            {
                "fullUrl": f"urn:uuid:{patient_id}",
                "resource": patient_resource
            }
        ]

        # Conditions
        for cond in extracted_data.get("conditions", []):
            cond_dict = cond if isinstance(cond, dict) else {"name": str(cond)}
            res = self.build_condition_resource(cond_dict, patient_id)
            entries.append({
                "fullUrl": f"urn:uuid:{res['id']}",
                "resource": res
            })

        # Medications
        for med in extracted_data.get("medications", []):
            med_dict = med if isinstance(med, dict) else {"name": str(med)}
            res = self.build_medication_request_resource(med_dict, patient_id)
            entries.append({
                "fullUrl": f"urn:uuid:{res['id']}",
                "resource": res
            })

        # Observations / Labs
        for lab in extracted_data.get("labs", []):
            lab_dict = lab if isinstance(lab, dict) else {"test_name": str(lab)}
            res = self.build_observation_resource(lab_dict, patient_id)
            entries.append({
                "fullUrl": f"urn:uuid:{res['id']}",
                "resource": res
            })

        bundle = {
            "resourceType": "Bundle",
            "id": str(uuid.uuid4()),
            "type": bundle_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entry": entries
        }

        self.validate_bundle_schema(bundle)
        return bundle

    def validate_bundle_schema(self, bundle: Dict[str, Any]) -> bool:
        """
        Validates structural schema compliance of the FHIR R4 Bundle.
        """
        if not isinstance(bundle, dict):
            raise FHIRValidationError("FHIR Bundle must be a dictionary object")

        if bundle.get("resourceType") != "Bundle":
            raise FHIRValidationError(f"Invalid resourceType '{bundle.get('resourceType')}', expected 'Bundle'")

        if bundle.get("type") not in ["transaction", "collection", "document", "message", "batch"]:
            raise FHIRValidationError(f"Invalid bundle type '{bundle.get('type')}'")

        entries = bundle.get("entry")
        if not isinstance(entries, list):
            raise FHIRValidationError("FHIR Bundle 'entry' field must be a list")

        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise FHIRValidationError(f"Bundle entry[{idx}] must be a dict")
            if "fullUrl" not in entry and "resource" not in entry:
                raise FHIRValidationError(f"Bundle entry[{idx}] missing mandatory 'fullUrl' or 'resource'")
            res = entry.get("resource")
            if not isinstance(res, dict) or "resourceType" not in res or "id" not in res:
                raise FHIRValidationError(f"Bundle entry[{idx}] resource invalid or missing 'resourceType'/'id'")

        return True

    # ── Backward Compatibility Classmethods ───────────────────────────────────

    @classmethod
    def to_fhir_patient(cls, patient_id: str, name: str = "John Smith", gender: str = "male", birth_date: str = "1960-01-01") -> Dict[str, Any]:
        return cls().build_patient_resource({"id": patient_id, "name": name, "gender": gender, "birthDate": birth_date})

    @classmethod
    def to_fhir_condition(cls, condition_name: str, icd10_code: str = None, snomed_code: str = None) -> Dict[str, Any]:
        return cls().build_condition_resource({"name": condition_name, "icd10": icd10_code}, "patient-001")

    @classmethod
    def to_fhir_medication_request(cls, med: Dict[str, Any], patient_id: str = "patient-001") -> Dict[str, Any]:
        return cls().build_medication_request_resource(med, patient_id)

    @classmethod
    def create_fhir_transaction_bundle(cls, patient_id: str, diseases: List[str], medications: List[Dict[str, Any]]) -> Dict[str, Any]:
        data = {
            "patient": {"id": patient_id},
            "conditions": diseases,
            "medications": medications
        }
        return cls().create_bundle(data, bundle_type="transaction")
