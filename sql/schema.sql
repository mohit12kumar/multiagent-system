-- Complete Database Schema for Multi-Agent Clinical Information Extraction & Decision Support System

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'patient', -- 'doctor', 'patient', 'admin'
    full_name VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NULL,
    content TEXT NOT NULL,
    redacted_content TEXT NULL,
    meta_data JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS pipeline_sessions (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    status VARCHAR(50) NOT NULL, -- PENDING, IN_PROGRESS, COMPLETED, FAILED
    current_stage VARCHAR(50) NOT NULL,
    error_message TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS canonical_entities (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL, -- DISEASE, DRUG, SYMPTOM, ANATOMY, PROCEDURE
    description TEXT NULL,
    wikidata_id VARCHAR(50) NULL,
    rxnorm_id VARCHAR(50) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS entity_mentions (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    text VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    start_char INT NOT NULL,
    end_char INT NOT NULL,
    confidence FLOAT NOT NULL,
    source_agents VARCHAR(255) NOT NULL,
    canonical_id VARCHAR(36) NULL,
    needs_review BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES pipeline_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (canonical_id) REFERENCES canonical_entities(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS disease_relations (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    disease_name VARCHAR(255) NOT NULL,
    symptom_name VARCHAR(255) NOT NULL,
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES pipeline_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS medication_relations (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    disease_name VARCHAR(255) NOT NULL,
    medication_name VARCHAR(255) NOT NULL,
    correct BOOLEAN DEFAULT TRUE,
    confidence FLOAT NOT NULL,
    dosage VARCHAR(100) NULL,
    frequency VARCHAR(100) NULL,
    duration VARCHAR(100) NULL,
    route VARCHAR(100) NULL,
    validation_status VARCHAR(50) NULL, -- 'Correct Medication', 'Alternative Medication', 'Unknown Medication'
    validation_reason TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES pipeline_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_queue (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    entity_mention_id VARCHAR(36) NULL,
    medication_relation_id VARCHAR(36) NULL,
    status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED, MODIFIED
    reason TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES pipeline_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (entity_mention_id) REFERENCES entity_mentions(id) ON DELETE CASCADE,
    FOREIGN KEY (medication_relation_id) REFERENCES medication_relations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_logs (
    id VARCHAR(36) PRIMARY KEY,
    entity_mention_id VARCHAR(36) NULL,
    review_queue_id VARCHAR(36) NULL,
    reviewer VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL, -- APPROVED, REJECTED, MODIFIED, APPROVED_ALL
    old_value TEXT NULL,
    new_value TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patient_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    summary_json JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES pipeline_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS phi_audit_log (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    field_type VARCHAR(50) NOT NULL,
    original_value VARCHAR(255) NOT NULL,
    redacted_value VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES pipeline_sessions(id) ON DELETE CASCADE
);
