export interface User {
  id?: string;
  username: string;
  email?: string;
  role: 'doctor' | 'patient';
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface DashboardData {
  total_patients: number;
  total_extractions: number;
  diseases_detected: number;
  completed_sessions: number;
  pending_review_count: number;
  approved_review_count: number;
  total_entities: number;
  medication_accuracy: number;
  average_confidence: string;
  average_processing_time: string;
  review_approval_rate: string;
  most_common_diseases: Array<{ name: string; count: number }>;
  most_common_medications: Array<{ name: string; count: number }>;
}

export interface ReviewQueueItem {
  id: string;
  session_id: string;
  status: 'PENDING' | 'RESOLVED' | 'REJECTED' | 'APPROVED';
  reason: string;
  created_at: string;
  details?: {
    type?: string;
    text?: string;
    entity_type?: string;
    confidence?: number;
    source_agents?: string;
    disease?: string;
    medication?: string;
    dosage?: string;
    frequency?: string;
    duration?: string;
    validation_status?: string;
    raw_note?: string;
    patient_name?: string;
    patient_user_id?: string;
    patient_summary?: any[];
  };
}

export interface PatientHistoryRecord {
  history_id: string;
  user_id: string;
  patient_name: string;
  patient_id: string;
  session_id: string;
  summary: any;
  raw_note: string;
  created_at: string;
}

// Real backend extraction response structure
export interface ExtractionResponse {
  session_id: string;
  document_id: string;
  status?: string;
  patient_message?: string;

  // Actual fields returned by the AI pipeline
  symptoms?: string[];
  diseases?: string[];
  medications?: string[];
  laboratory_values?: any[];
  vital_signs_interpreted?: any[];
  allergies?: string[];
  procedures?: string[];
  differential_diagnoses?: any[];
  drug_interactions?: any[];
  clinical_warnings?: string[];

  // Structured summaries
  patient_summary?: {
    name?: string;
    age?: string;
    gender?: string;
    structured_summary?: any[];
    clinical_notes_overview?: string;
  };
  overall_clinical_summary?: {
    diseases_detected?: string[];
    disease_count?: number;
    overall_risk?: string;
    review_status?: string;
    summary_statement?: string;
  };

  // Risk & scores
  organ_risk?: {
    overall_risk_level?: string;
    cardiac_risk?: string;
    mortality_prediction?: string;
  };
  clinical_quality_score?: string;
  confidence_scores?: {
    overall_consensus?: string;
    disease_confidence?: string;
  };

  // Doctor review
  doctor_review_required?: boolean;
  doctor_report?: string;
  triage_info?: {
    badge?: string;
    level?: string;
  };

  // Additional
  fhir_bundle?: any;
  knowledge_graph?: any;
  recommendations?: any[];
  guideline_medication_recommendations?: any[];
  missing_information?: any;
  metadata?: {
    execution_time_seconds?: number;
    api_calls_count?: number;
  };
  performance_metrics?: {
    total_processing_time?: number;
  };
  observability?: {
    execution_time_seconds?: number;
  };

  // Legacy fields (kept for compatibility)
  entities?: any[];
  relations?: any[];
}
