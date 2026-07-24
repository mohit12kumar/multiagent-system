import pytest
from backend.clinical.medication_coverage_checker import MedicationCoverageChecker
from backend.clinical.final_clinical_validator import FinalClinicalValidator
from backend.clinical.quality_audit_report import QualityAuditReportGenerator

def test_medication_coverage_checker():
    raw_mentions = ["Amlodipine", "Metformin", "Salbutamol"]
    med_relations = [
        {"name": "Amlodipine", "disease_name": "Hypertension"},
        {"name": "Metformin", "disease_name": "Diabetes"}
    ]
    rejected = ["Salbutamol"]
    
    audit = MedicationCoverageChecker.audit_coverage(raw_mentions, med_relations, rejected)
    assert audit["total_detected"] == 3
    assert audit["mapped_count"] == 2
    assert audit["coverage_percentage"] == 100.0
    assert audit["audit_passed"] is True

def test_final_clinical_validator():
    sample_output = {
        "diseases": ["Hypertension"],
        "medications": ["Amlodipine"],
        "patient_summary": {
            "structured_summary": [
                {
                    "disease": "Hypertension",
                    "icd10": "I10",
                    "confidence": 0.95,
                    "detected_because": ["Elevated Blood Pressure"],
                    "symptoms": ["headache"],
                    "medications": [
                        {"name": "Amlodipine", "dosage": "5 mg", "route": "PO (Oral)"}
                    ]
                }
            ]
        }
    }
    
    val_result = FinalClinicalValidator.validate_pipeline_output(sample_output)
    assert val_result["is_valid"] is True
    assert val_result["doctor_review_forced"] is True

def test_quality_audit_report_generator():
    sample_output = {
        "diseases": ["Hypertension"],
        "medications": ["Amlodipine"],
        "patient_summary": {
            "structured_summary": [
                {
                    "disease": "Hypertension",
                    "icd10": "I10",
                    "confidence": 0.95,
                    "symptoms": ["headache"],
                    "medications": [
                        {"name": "Amlodipine", "dosage": "5 mg", "route": "PO (Oral)"}
                    ]
                }
            ]
        }
    }
    val_result = {"is_valid": True, "validation_warnings": []}
    cov_audit = {"coverage_percentage": 100.0}
    
    report = QualityAuditReportGenerator.generate_report(sample_output, val_result, cov_audit)
    assert report["report_type"] == "INTERNAL_QUALITY_AUDIT"
    assert report["quality_rating"] == "ENTERPRISE_GRADE_A"
