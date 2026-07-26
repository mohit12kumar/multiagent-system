from pydantic import BaseModel, Field
from typing import Optional, List


class DiseaseRelationModel(BaseModel):
    id: Optional[str] = None
    disease_name: str
    symptom_name: str
    confidence: float = 1.0


class MedicationDetailModel(BaseModel):
    name: str
    disease_name: Optional[str] = None  # Which disease this medication is linked to
    correct: bool = True
    confidence: float = 1.0
    dosage: Optional[str] = "N/A"
    dosage_unit: Optional[str] = "mg"
    frequency: Optional[str] = "N/A"
    duration: Optional[str] = "N/A"
    route: Optional[str] = "Oral"
    formulation: Optional[str] = "Tablet"
    completeness_score: Optional[int] = 100
    clinical_warning: Optional[str] = None
    validation_status: Optional[str] = "Correct Medication"
    validation_reason: Optional[str] = None


class DiseaseSummaryModel(BaseModel):
    disease: str
    symptoms: List[str] = Field(default_factory=list)
    medication: Optional[MedicationDetailModel] = None
    all_medications: Optional[List[MedicationDetailModel]] = Field(default_factory=list)
    confidence: Optional[float] = 0.95
    detected_because: Optional[List[str]] = Field(default_factory=list)
    evidence_scores: Optional[dict] = Field(default_factory=dict)



class StructuredPatientSummaryResponse(BaseModel):
    patient_summary: List[DiseaseSummaryModel] = Field(default_factory=list)
    doctor_report: Optional[str] = None
    patient_narrative: Optional[str] = None
