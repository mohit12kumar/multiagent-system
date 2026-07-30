# Disaster Recovery Runbook & Backup Guidelines

## Overview
This runbook defines disaster recovery (DR) procedures for the Enterprise Clinical Intelligence Platform to ensure business continuity, data integrity, and compliance with healthcare regulations (HIPAA/GDPR).

---

## Recovery Time & Point Objectives
- **Recovery Time Objective (RTO)**: < 2 hours (Time to bring system back online after failure)
- **Recovery Point Objective (RPO)**: < 1 hour (Maximum acceptable data loss window)

---

## Backup Schedules

### 1. Database Automated Backups (MySQL)
- **Frequency**: Every 1 hour (incremental binlogs), Daily at 01:00 UTC (full dump).
- **Retention**: Daily backups kept for 30 days; monthly snapshots kept for 7 years (regulatory compliance).

#### Daily Backup Command (Automated Cron Script):
```bash
mysqldump -h localhost -u root -p'PASSWORD' \
  --single-transaction \
  --routines \
  --triggers \
  --quick \
  clinical_multiagent | gzip > /backups/mysql/clinical_db_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 2. Vector Store Snapshot (ChromaDB)
- **Frequency**: Daily at 02:00 UTC
- **Path**: `chroma_db/` directory

```bash
tar -czvf /backups/chroma/chroma_db_$(date +%Y%m%d_%H%M%S).tar.gz d:/office project/multiagent_system/chroma_db
```

---

## Restore Procedure & Verification

### Database Restore Steps:
1. Stop backend service API processes.
2. Create empty target database if missing:
   ```sql
   CREATE DATABASE IF NOT EXISTS clinical_multiagent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. Import backup file:
   ```bash
   gunzip < /backups/mysql/clinical_db_20260730.sql.gz | mysql -u root -p clinical_multiagent
   ```
4. Verify audit table hash chain integrity:
   ```python
   # Verify cryptographic audit chain continuity
   from backend.services.audit_service import AuditLog
   # Verify previous_hash == SHA256(last_entry)
   ```

5. Restart FastAPI service:
   ```bash
   python -m uvicorn backend.api.routes:app --reload
   ```

---

## Failover & Health Checks
- Verify health status endpoint: `GET /api/health`
- Verify metrics endpoint: `GET /metrics`
