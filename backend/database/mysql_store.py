import uuid
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.database.models import (
    User, Document, PipelineSession, EntityMention, CanonicalEntity,
    DiseaseRelation, MedicationRelation, ReviewQueue, ReviewLog,
    PatientHistory, PHIAuditLog
)

logger = logging.getLogger(__name__)


class MySQLStore:
    def __init__(self, db_session: Session):
        self.db = db_session

    # User Auth CRUD
    def create_user(self, username: str, email: str, hashed_password: str, role: str = "patient", full_name: Optional[str] = None) -> User:
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
            full_name=full_name
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    # Document & Session CRUD
    def create_document(self, doc_id: str, content: str, meta_data: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None) -> Document:
        doc = Document(
            id=doc_id,
            user_id=user_id,
            content=content,
            meta_data=meta_data or {}
        )
        self.db.add(doc)
        self.db.commit()
        return doc

    def create_session(self, session_id: str, doc_id: str) -> PipelineSession:
        session = PipelineSession(
            id=session_id,
            document_id=doc_id,
            status="PENDING",
            current_stage="INITIALIZING"
        )
        self.db.add(session)
        self.db.commit()
        return session

    def update_session(self, session_id: str, status: str, stage: str, error_message: Optional[str] = None):
        session = self.db.query(PipelineSession).filter(PipelineSession.id == session_id).first()
        if session:
            session.status = status
            session.current_stage = stage
            if error_message:
                session.error_message = error_message
            self.db.commit()

    def save_phi_audit(self, session_id: str, phi_items: List[Dict[str, Any]]):
        """Stage add only — called within save_pipeline_results() transaction."""
        for item in phi_items:
            audit = PHIAuditLog(
                id=str(uuid.uuid4()),
                session_id=session_id,
                field_type=item.get("entity_type", "SENSITIVE_TEXT"),
                original_value=item.get("original", ""),
                redacted_value=item.get("redacted", "[REDACTED]")
            )
            self.db.add(audit)
        # No commit here — called within atomic transaction

    def save_entity_mentions(self, session_id: str, doc_id: str, mentions: List[Dict[str, Any]]):
        """Stage add only — called within save_pipeline_results() transaction."""
        for mention in mentions:
            m_id = str(uuid.uuid4())
            sources = mention.get("source_agents", [])
            source_str = ",".join(sources) if isinstance(sources, list) else str(sources)

            needs_review = mention.get("needs_review", False)
            em = EntityMention(
                id=m_id,
                document_id=doc_id,
                session_id=session_id,
                text=mention.get("text", ""),
                type=mention.get("type", "UNKNOWN"),
                start_char=mention.get("start_char", 0),
                end_char=mention.get("end_char", 0),
                confidence=float(mention.get("confidence", 1.0)),
                source_agents=source_str,
                canonical_id=mention.get("canonical_id"),
                needs_review=needs_review
            )
            self.db.add(em)

            if needs_review:
                rq = ReviewQueue(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    entity_mention_id=m_id,
                    status="PENDING",
                    reason="Low confidence extraction"
                )
                self.db.add(rq)
        # No commit here — called within atomic transaction

    def save_disease_relations(self, session_id: str, disease_relations: List[Any]):
        """Stage add only — called within save_pipeline_results() transaction."""
        for rel in disease_relations:
            if isinstance(rel, dict):
                dis_name = rel.get("disease_name", "")
                sym_name = rel.get("symptom_name", "")
                conf = float(rel.get("confidence", 1.0))
            else:
                dis_name = getattr(rel, "disease_name", "")
                sym_name = getattr(rel, "symptom_name", "")
                conf = float(getattr(rel, "confidence", 1.0))

            dr = DiseaseRelation(
                id=str(uuid.uuid4()),
                session_id=session_id,
                disease_name=dis_name,
                symptom_name=sym_name,
                confidence=conf
            )
            self.db.add(dr)
        # No commit here — called within atomic transaction

    def save_medication_relations(self, session_id: str, medication_relations: List[Any]):
        """Stage add only — called within save_pipeline_results() transaction."""
        for rel in medication_relations:
            mr_id = str(uuid.uuid4())
            if isinstance(rel, dict):
                disease_name = rel.get("disease_name") or "General Condition"
                med_name = rel.get("name", rel.get("medication_name", "")) or "Medication"
                correct = rel.get("correct", True)
                confidence = float(rel.get("confidence", 1.0))
                dosage = rel.get("dosage") or "N/A"
                frequency = rel.get("frequency") or "N/A"
                duration = rel.get("duration") or "N/A"
                route = rel.get("route") or "Oral"
                val_status = str(rel.get("validation_status", "Correct Medication"))[:45]
                val_reason = rel.get("validation_reason", None)
            else:
                disease_name = getattr(rel, "disease_name", None) or "General Condition"
                med_name = getattr(rel, "name", None) or getattr(rel, "medication_name", None) or "Medication"
                correct = getattr(rel, "correct", True)
                confidence = float(getattr(rel, "confidence", 1.0))
                dosage = getattr(rel, "dosage", None) or "N/A"
                frequency = getattr(rel, "frequency", None) or "N/A"
                duration = getattr(rel, "duration", None) or "N/A"
                route = getattr(rel, "route", "Oral")
                val_status = str(getattr(rel, "validation_status", "Correct Medication"))[:45]
                val_reason = getattr(rel, "validation_reason", None)

            mr = MedicationRelation(
                id=mr_id,
                session_id=session_id,
                disease_name=disease_name,
                medication_name=med_name,
                correct=correct,
                confidence=confidence,
                dosage=dosage,
                frequency=frequency,
                duration=duration,
                route=route,
                validation_status=val_status,
                validation_reason=val_reason
            )
            self.db.add(mr)

            if not correct or confidence < 0.75:
                rq = ReviewQueue(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    medication_relation_id=mr_id,
                    status="PENDING",
                    reason=f"Medication validation review ({val_status})"
                )
                self.db.add(rq)
        # No commit here — called within atomic transaction

    def save_patient_history(self, user_id: str, session_id: str, summary_json: Any) -> PatientHistory:
        """Stage add only — called within save_pipeline_results() transaction."""
        ph = PatientHistory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            summary_json=summary_json
        )
        self.db.add(ph)
        # No commit here — called within atomic transaction
        return ph

    def save_session_review_entry(self, session_id: str, user_id: Optional[str] = None) -> ReviewQueue:
        """Creates a session-level ReviewQueue entry. Stage add only — no commit."""
        # Avoid duplicate session-level review entries
        existing = self.db.query(ReviewQueue).filter(
            ReviewQueue.session_id == session_id,
            ReviewQueue.entity_mention_id == None,
            ReviewQueue.medication_relation_id == None
        ).first()
        if existing:
            return existing

        rq = ReviewQueue(
            id=str(uuid.uuid4()),
            session_id=session_id,
            entity_mention_id=None,
            medication_relation_id=None,
            status="PENDING",
            reason=f"Patient-submitted clinical note — awaiting doctor pre-check (user: {user_id or 'anonymous'})"
        )
        self.db.add(rq)
        # No commit here — called within atomic transaction
        return rq

    def save_pipeline_results(
        self,
        session_id: str,
        doc_id: str,
        entity_mentions: List[Dict[str, Any]],
        disease_relations: List[Any],
        medication_relations: List[Any],
        patient_summary: Any,
        user_id: str,
    ) -> None:
        """
        Atomically persist all pipeline output in a single DB transaction.

        If any step fails, the entire transaction rolls back — preventing partial
        state where e.g. diseases are saved but medications are not.

        Parameters
        ----------
        session_id       : Pipeline session UUID.
        doc_id           : Document UUID.
        entity_mentions  : List of entity mention dicts from pipeline state.
        disease_relations: List of disease relation objects/dicts.
        medication_relations: List of medication relation objects/dicts.
        patient_summary  : Formatted patient summary list for PatientHistory.
        user_id          : Authenticated user ID (or 'anonymous_patient').
        """
        from backend.core.retry import with_db_retry
        def _do_save():
            try:
                self.save_entity_mentions(session_id, doc_id, entity_mentions)
                self.save_disease_relations(session_id, disease_relations)
                self.save_medication_relations(session_id, medication_relations)
                self.save_patient_history(user_id, session_id, patient_summary)
                self.save_session_review_entry(session_id, user_id=user_id)
                # Single commit — all or nothing
                self.db.commit()
                logger.info(f"[MySQLStore] Atomic pipeline results saved | session={session_id}")
            except Exception as e:
                self.db.rollback()
                logger.error(
                    f"[MySQLStore] Atomic save failed, rolled back | session={session_id} | error={e}",
                    exc_info=True
                )
                raise e

        with_db_retry(_do_save, label=f"Save Pipeline Results ({session_id})")

    # Canonical Entity CRUD
    def get_or_create_canonical_entity(self, name: str, entity_type: str, wikidata_id: Optional[str] = None, rxnorm_id: Optional[str] = None) -> CanonicalEntity:
        entity = self.db.query(CanonicalEntity).filter(CanonicalEntity.name == name).first()
        if not entity:
            entity = CanonicalEntity(
                id=str(uuid.uuid4()),
                name=name,
                type=entity_type,
                wikidata_id=wikidata_id,
                rxnorm_id=rxnorm_id
            )
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
        return entity

    # Review Queue & Analytics
    def get_pending_review_queue(self) -> List[Dict[str, Any]]:
        items = self.db.query(ReviewQueue).filter(ReviewQueue.status == "PENDING").all()
        results = []
        for item in items:
            mention_data = None
            if item.entity_mention:
                em = item.entity_mention
                mention_data = {
                    "type": "entity_mention",
                    "text": em.text,
                    "entity_type": em.type,
                    "confidence": em.confidence,
                    "source_agents": em.source_agents
                }
            elif item.medication_relation:
                mr = item.medication_relation
                mention_data = {
                    "type": "medication_relation",
                    "disease": mr.disease_name,
                    "medication": mr.medication_name,
                    "correct": mr.correct,
                    "confidence": mr.confidence,
                    "dosage": mr.dosage,
                    "frequency": mr.frequency,
                    "duration": mr.duration,
                    "validation_status": mr.validation_status,
                    "validation_reason": mr.validation_reason
                }
            else:
                # Session-level review entry — enrich with document & patient summary
                session = item.session
                doc_content = ""
                patient_summary = []
                patient_user_id = None
                patient_username = "Patient"
                if session:
                    if session.document:
                        doc_content = session.document.content or ""
                    ph = self.db.query(PatientHistory).filter(
                        PatientHistory.session_id == session.id
                    ).first()
                    if ph:
                        patient_summary = ph.summary_json or []
                        patient_user_id = ph.user_id
                        if ph.user:
                            patient_username = ph.user.full_name or ph.user.username
                mention_data = {
                    "type": "patient_submission",
                    "raw_note": doc_content,
                    "patient_user_id": patient_user_id,
                    "patient_name": patient_username,
                    "patient_summary": patient_summary
                }


            results.append({
                "id": item.id,
                "session_id": item.session_id,
                "status": item.status,
                "reason": item.reason,
                "created_at": item.created_at.isoformat() + "Z" if item.created_at else None,
                "details": mention_data
            })
        return results

    def resolve_review_item(
        self,
        review_id: str,
        action: str,
        reviewer: str,
        new_value: Optional[str] = None,
        expected_version: int = 0,
    ) -> bool:
        """
        Resolve a review queue item with optimistic locking.

        Parameters
        ----------
        review_id        : ReviewQueue primary key.
        action           : 'APPROVE', 'REJECT', or 'MODIFY'.
        reviewer         : Display name of the resolving doctor.
        new_value        : Updated text/name (for MODIFY action).
        expected_version : The version_number the caller read when loading the item.
                           If the DB version differs, a concurrent update is detected.

        Returns
        -------
        bool  — True on success.
        Raises ConcurrentUpdateError if the item was concurrently modified.
        Raises ValueError if item not found.
        """
        import datetime as _dt
        from backend.core.exceptions import ConcurrentUpdateError

        # with_for_update() places a row-level lock (SELECT FOR UPDATE)
        # preventing another concurrent transaction from modifying this row.
        item = (
            self.db.query(ReviewQueue)
            .filter(ReviewQueue.id == review_id, ReviewQueue.is_deleted == False)
            .with_for_update()
            .first()
        )
        if not item:
            return False

        # Optimistic version check
        if item.version_number != expected_version:
            raise ConcurrentUpdateError(
                f"Review item '{review_id}' was modified by another user. "
                f"Expected version {expected_version}, found {item.version_number}. "
                f"Please refresh and try again."
            )

        # Increment version on every mutation
        item.version_number += 1
        item.reviewed_by = reviewer
        item.reviewed_at = _dt.datetime.now(_dt.timezone.utc)
        item.status = "RESOLVED" if action in ("APPROVED", "MODIFIED") else "REJECTED"

        old_val = ""
        if item.entity_mention:
            old_val = item.entity_mention.text
            if action == "MODIFIED" and new_value:
                item.entity_mention.text = new_value
        elif item.medication_relation:
            old_val = (
                f"{item.medication_relation.medication_name} "
                f"for {item.medication_relation.disease_name}"
            )
            if action == "APPROVED":
                item.medication_relation.correct = True
            elif action == "REJECTED":
                item.medication_relation.correct = False
            elif action == "MODIFIED" and new_value:
                item.medication_relation.medication_name = new_value

        log = ReviewLog(
            id=str(uuid.uuid4()),
            review_queue_id=item.id,
            reviewer=reviewer,
            action=action,
            old_value=old_val,
            new_value=new_value,
        )
        self.db.add(log)

        # Update parent PipelineSession when all pending items are resolved
        remaining_pending = (
            self.db.query(ReviewQueue)
            .filter(
                ReviewQueue.session_id == item.session_id,
                ReviewQueue.status == "PENDING",
                ReviewQueue.is_deleted == False,
                ReviewQueue.id != item.id,
            )
            .count()
        )
        if remaining_pending == 0:
            session = (
                self.db.query(PipelineSession)
                .filter(PipelineSession.id == item.session_id)
                .first()
            )
            if session:
                session.status = "COMPLETED"

        self.db.commit()
        logger.info(
            f"[MySQLStore] Review {review_id} resolved | action={action} "
            f"| reviewer={reviewer} | version={item.version_number}"
        )
        return True

    def approve_all_pending_reviews(self, reviewer: str) -> int:
        """
        Bulk-approve all pending review items.
        Soft-deleted items are excluded.
        """
        import datetime as _dt

        pending_items = (
            self.db.query(ReviewQueue)
            .filter(ReviewQueue.status == "PENDING", ReviewQueue.is_deleted == False)
            .with_for_update()
            .all()
        )
        count = len(pending_items)
        session_ids = set()
        now = _dt.datetime.now(_dt.timezone.utc)

        for item in pending_items:
            item.status         = "RESOLVED"
            item.reviewed_by    = reviewer
            item.reviewed_at    = now
            item.version_number = item.version_number + 1
            session_ids.add(item.session_id)
            if item.medication_relation:
                item.medication_relation.correct = True
            log = ReviewLog(
                id=str(uuid.uuid4()),
                review_queue_id=item.id,
                reviewer=reviewer,
                action="APPROVED_ALL",
            )
            self.db.add(log)

        for sid in session_ids:
            session = (
                self.db.query(PipelineSession)
                .filter(PipelineSession.id == sid)
                .first()
            )
            if session:
                session.status = "COMPLETED"

        self.db.commit()
        logger.info(
            f"[MySQLStore] Bulk approved {count} pending reviews | reviewer={reviewer}"
        )
        return count
