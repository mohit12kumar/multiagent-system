# HIPAA & GDPR Data Retention & Erasure Policy

## 1. Regulatory Context
The Enterprise Clinical Intelligence Platform processes Protected Health Information (PHI) subject to HIPAA (US), GDPR (EU), and local medical record privacy acts. This document establishes technical rules for data retention, soft deletion, and patient-requested erasure.

---

## 2. Retention Schedules

| Data Category | Storage Table | Retention Period | Deletion Method |
|---------------|---------------|------------------|-----------------|
| Clinical Notes & Uploaded Documents | `documents` | 7 Years | Soft Delete → Scheduled Hard Delete |
| Extracted NER Entities & Relations | `entity_mentions`, `disease_relations`, `medication_relations` | 7 Years | Soft Delete via Cascade |
| Doctor Review Queue History | `review_queue`, `review_logs` | 7 Years | Immutable Audit Archive |
| Cryptographic Audit Trail | `audit_logs` | Permanent (Min 7 Years) | Append-only (Never Deleted) |
| User Accounts & Access Logs | `users` | Account Lifetime + 3 Years | Soft Delete (`is_active=False`) |

---

## 3. Technical Safeguards & Implementation

### Soft Delete Pattern
Records marked for deletion receive:
- `is_deleted = True`
- `deleted_at = UTC Timestamp`
- `deleted_by = Actor User ID`

Queries in `MySQLStore` default to filtering `is_deleted = False` to prevent deleted records from appearing in patient or doctor views.

### Cryptographic Audit Integrity
All modifications to patient records emit an immutable `AuditLog` entry featuring:
- `previous_hash`: Cryptographic SHA-256 hash of the preceding log row
- `current_hash`: Cryptographic SHA-256 hash of the current log row

This guarantees tamper-evident logging for compliance audits.
