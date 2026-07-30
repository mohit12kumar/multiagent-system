"""
backend/services/audit_service.py

Structured audit logging for the Clinical Multi-Agent System.

Every action that modifies patient data, changes a review decision, authenticates
a user, or exports records is logged to the `audit_logs` table via this service.

This provides:
  - Regulatory compliance (HIPAA audit trail requirement)
  - Forensic capability (who changed what, when, from which IP)
  - Non-repudiation for doctor review decisions

Usage:
    from backend.services.audit_service import log_action

    log_action(
        db=db,
        actor_user_id=current_user["user_id"],
        action="REVIEW_APPROVE",
        resource_type="ReviewQueue",
        resource_id=review_id,
        old_value=old_status,
        new_value="APPROVED",
        ip_address=request.client.host,
    )
"""

import datetime
import logging
import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session
from backend.database.models import AuditLog

logger = logging.getLogger(__name__)

# ── Recognised action constants ────────────────────────────────────────────────
# Import these constants to avoid typos in callers.

ACTION_LOGIN_SUCCESS  = "LOGIN_SUCCESS"
ACTION_LOGIN_FAILED   = "LOGIN_FAILED"
ACTION_LOGOUT         = "LOGOUT"
ACTION_REGISTER       = "USER_REGISTER"
ACTION_NOTE_SUBMIT    = "NOTE_SUBMIT"
ACTION_REVIEW_APPROVE = "REVIEW_APPROVE"
ACTION_REVIEW_REJECT  = "REVIEW_REJECT"
ACTION_REVIEW_MODIFY  = "REVIEW_MODIFY"
ACTION_APPROVE_ALL    = "REVIEW_APPROVE_ALL"
ACTION_PDF_EXPORT     = "PDF_EXPORT"
ACTION_JSON_EXPORT    = "JSON_EXPORT"
ACTION_PIPELINE_START = "PIPELINE_START"
ACTION_PIPELINE_END   = "PIPELINE_END"


def log_action(
    db: Session,
    action: str,
    *,
    actor_user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id:   Optional[str] = None,
    old_value:     Any = None,
    new_value:     Any = None,
    ip_address:    Optional[str] = None,
    notes:         Optional[str] = None,
) -> None:
    """
    Write a structured audit log entry to the database.

    This function is intentionally non-raising — audit logging must never
    cause a primary business operation to fail. Errors are logged to the
    application logger but silently swallowed.

    Parameters
    ----------
    db            : SQLAlchemy session for the current request.
    action        : String action code (use ACTION_* constants above).
    actor_user_id : UUID of the user performing the action (None = system).
    resource_type : Table/entity type being modified (e.g. "ReviewQueue").
    resource_id   : Primary key of the affected record.
    old_value     : Previous value (serialised to string).
    new_value     : New value (serialised to string).
    ip_address    : Client IP address from request.client.host.
    notes         : Additional human-readable context.
    """
    try:
        import hashlib
        # Fetch last audit entry to chain cryptographic hash
        last_entry = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()
        prev_hash = last_entry.current_hash if (last_entry and last_entry.current_hash) else "GENESIS_BLOCK_HASH_CLINICAL_SYSTEM"

        entry_id = str(uuid.uuid4())
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        payload_str = f"{entry_id}|{actor_user_id}|{action}|{resource_type}|{resource_id}|{now_dt.isoformat()}|{prev_hash}"
        curr_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        entry = AuditLog(
            id            = entry_id,
            actor_user_id = actor_user_id,
            action        = action,
            resource_type = resource_type,
            resource_id   = resource_id,
            old_value     = str(old_value)  if old_value  is not None else None,
            new_value     = str(new_value)  if new_value  is not None else None,
            ip_address    = ip_address,
            notes         = notes,
            previous_hash = prev_hash,
            current_hash  = curr_hash,
            timestamp     = now_dt,
        )
        db.add(entry)
        db.commit()
        logger.debug(
            f"[Audit] {action} | actor={actor_user_id} | "
            f"{resource_type}:{resource_id} | hash={curr_hash[:8]}"
        )
    except Exception as exc:
        # Audit logging must never break the primary operation.
        # Log the failure and continue.
        logger.error(f"[Audit] Failed to write audit log entry: {exc}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
