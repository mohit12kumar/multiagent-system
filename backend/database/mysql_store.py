import uuid
import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.database.models import (
    User, Document, PipelineSession, EntityMention, CanonicalEntity,
    DiseaseRelation, MedicationRelation, ReviewQueue, ReviewLog,
    PatientHistory, PHIAuditLog
)


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
        for item in phi_items:
            audit = PHIAuditLog(
                id=str(uuid.uuid4()),
                session_id=session_id,
                field_type=item.get("entity_type", "SENSITIVE_TEXT"),
                original_value=item.get("original", ""),
                redacted_value=item.get("redacted", "[REDACTED]")
            )
            self.db.add(audit)
        self.db.commit()

    def save_entity_mentions(self, session_id: str, doc_id: str, mentions: List[Dict[str, Any]]):
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
        self.db.commit()

    def save_disease_relations(self, session_id: str, disease_relations: List[Any]):
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
        self.db.commit()

    def save_medication_relations(self, session_id: str, medication_relations: List[Any]):
        for rel in medication_relations:
            mr_id = str(uuid.uuid4())
            if isinstance(rel, dict):
                disease_name = rel.get("disease_name", "")
                med_name = rel.get("name", rel.get("medication_name", ""))
                correct = rel.get("correct", True)
                confidence = float(rel.get("confidence", 1.0))
                dosage = rel.get("dosage", "N/A")
                frequency = rel.get("frequency", "N/A")
                duration = rel.get("duration", "N/A")
                route = rel.get("route", "Oral")
                val_status = str(rel.get("validation_status", "Correct Medication"))[:45]
                val_reason = rel.get("validation_reason", None)
            else:
                disease_name = getattr(rel, "disease_name", "")
                med_name = getattr(rel, "name", getattr(rel, "medication_name", ""))
                correct = getattr(rel, "correct", True)
                confidence = float(getattr(rel, "confidence", 1.0))
                dosage = getattr(rel, "dosage", "N/A")
                frequency = getattr(rel, "frequency", "N/A")
                duration = getattr(rel, "duration", "N/A")
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
        self.db.commit()

    def save_patient_history(self, user_id: str, session_id: str, summary_json: Any):
        ph = PatientHistory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            summary_json=summary_json
        )
        self.db.add(ph)
        self.db.commit()
        return ph

    def save_session_review_entry(self, session_id: str, user_id: Optional[str] = None):
        """Creates a ReviewQueue entry for the whole session so the doctor can always see
        every patient-submitted note, even when all entity confidences pass the threshold."""
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
        self.db.commit()
        return rq

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

    def resolve_review_item(self, review_id: str, action: str, reviewer: str, new_value: Optional[str] = None) -> bool:
        item = self.db.query(ReviewQueue).filter(ReviewQueue.id == review_id).first()
        if not item:
            return False

        item.status = "RESOLVED" if action in ("APPROVED", "MODIFIED") else "REJECTED"
        old_val = ""

        if item.entity_mention:
            old_val = item.entity_mention.text
            if action == "MODIFIED" and new_value:
                item.entity_mention.text = new_value
        elif item.medication_relation:
            old_val = f"{item.medication_relation.medication_name} for {item.medication_relation.disease_name}"
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
            new_value=new_value
        )
        self.db.add(log)

        # Update parent PipelineSession status if all pending items resolved
        remaining_pending = self.db.query(ReviewQueue).filter(
            ReviewQueue.session_id == item.session_id,
            ReviewQueue.status == "PENDING",
            ReviewQueue.id != item.id
        ).count()
        if remaining_pending == 0:
            session = self.db.query(PipelineSession).filter(PipelineSession.id == item.session_id).first()
            if session:
                session.status = "COMPLETED"

        self.db.commit()
        return True

    def approve_all_pending_reviews(self, reviewer: str) -> int:
        pending_items = self.db.query(ReviewQueue).filter(ReviewQueue.status == "PENDING").all()
        count = len(pending_items)
        session_ids = set()
        for item in pending_items:
            item.status = "RESOLVED"
            session_ids.add(item.session_id)
            if item.medication_relation:
                item.medication_relation.correct = True
            log = ReviewLog(
                id=str(uuid.uuid4()),
                review_queue_id=item.id,
                reviewer=reviewer,
                action="APPROVED_ALL"
            )
            self.db.add(log)

        for sid in session_ids:
            session = self.db.query(PipelineSession).filter(PipelineSession.id == sid).first()
            if session:
                session.status = "COMPLETED"

        self.db.commit()
        return count
