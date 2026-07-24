import datetime
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from src.db.models import Document, PipelineSession, EntityMention, CanonicalEntity, ReviewQueue, PHIAuditLog
from src.monitoring.logger import logger


class MySQLStore:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_document(self, doc_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        """Saves a new raw document to MySQL."""
        doc = Document(
            id=doc_id,
            content=content,
            meta_data=metadata
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        logger.info(f"Saved document {doc_id} to MySQL")
        return doc

    def create_session(self, session_id: str, document_id: str) -> PipelineSession:
        """Saves a new pipeline session tracking state."""
        session = PipelineSession(
            id=session_id,
            document_id=document_id,
            status="PENDING",
            current_stage="PREPROCESSING"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        logger.info(
            f"Initialized pipeline session {session_id} for doc {document_id}")
        return session

    def update_session(self, session_id: str, status: str, stage: str, error_message: Optional[str] = None) -> PipelineSession:
        """Updates pipeline run state (replaces Redis state tracking)."""
        session = self.db.query(PipelineSession).filter(
            PipelineSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = status
        session.current_stage = stage
        if error_message:
            session.error_message = error_message
        session.updated_at = datetime.datetime.utcnow()

        self.db.commit()
        self.db.refresh(session)
        logger.info(
            f"Updated session {session_id}: status={status}, stage={stage}")
        return session

    def save_entity_mentions(self, session_id: str, document_id: str, mentions: List[Dict[str, Any]]) -> None:
        """Bulk inserts extracted entity mentions into MySQL database."""
        # Clean existing mentions for this session to support idempotency/reruns
        self.db.query(EntityMention).filter(
            EntityMention.session_id == session_id).delete()

        for m in mentions:
            mention_id = m.get("id") or str(uuid.uuid4())
            mention = EntityMention(
                id=mention_id,
                document_id=document_id,
                session_id=session_id,
                text=m["text"],
                type=m["type"],
                start_char=m["start_char"],
                end_char=m["end_char"],
                confidence=m["confidence"],
                source_agents=",".join(m.get("source_agents", [])),
                canonical_id=m.get("canonical_id")
            )
            self.db.add(mention)

            # If the mention has low confidence, flag it in the review queue
            if m.get("needs_review", False):
                review_item = ReviewQueue(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    entity_mention_id=mention_id,
                    status="PENDING"
                )
                self.db.add(review_item)

        self.db.commit()
        logger.info(
            f"Inserted {len(mentions)} entity mentions for session {session_id}")

    def get_canonical_entity_by_name(self, name: str) -> Optional[CanonicalEntity]:
        """Looks up a canonical entity by exact match name."""
        return self.db.query(CanonicalEntity).filter(CanonicalEntity.name == name).first()

    def get_canonical_entity_by_id(self, entity_id: str) -> Optional[CanonicalEntity]:
        """Looks up a canonical entity by ID."""
        return self.db.query(CanonicalEntity).filter(CanonicalEntity.id == entity_id).first()

    def create_canonical_entity(self, name: str, entity_type: str, description: Optional[str] = None, wikidata_id: Optional[str] = None) -> CanonicalEntity:
        """Creates a new canonical profile in MySQL."""
        entity_id = str(uuid.uuid4())
        entity = CanonicalEntity(
            id=entity_id,
            name=name,
            type=entity_type,
            description=description,
            wikidata_id=wikidata_id
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        logger.info(f"Created canonical entity {name} ({entity_id})")
        return entity

    def get_session_results(self, session_id: str, role: str = "doctor") -> Optional[Dict[str, Any]]:
        """Returns structured session results containing session status and all entity mentions."""
        session = self.db.query(PipelineSession).filter(
            PipelineSession.id == session_id).first()
        if not session:
            return None

        mentions = self.db.query(EntityMention).filter(
            EntityMention.session_id == session_id).all()

        entities_list = []
        for m in mentions:
            if role == "user" and m.review_queue_item and m.review_queue_item.status == "PENDING":
                continue
            entities_list.append({
                "id": m.id,
                "text": m.text,
                "type": m.type,
                "start_char": m.start_char,
                "end_char": m.end_char,
                "confidence": m.confidence,
                "source_agents": m.source_agents.split(",") if m.source_agents else [],
                "canonical_id": m.canonical_id,
                "canonical_name": m.canonical.name if m.canonical else None
            })

        return {
            "session_id": session.id,
            "document_id": session.document_id,
            "status": session.status,
            "current_stage": session.current_stage,
            "error_message": session.error_message,
            "created_at": session.created_at.isoformat() + "Z" if session.created_at else "",
            "updated_at": session.updated_at.isoformat() + "Z" if session.updated_at else "",
            "entities": entities_list
        }

    def get_sessions_by_patient_id(self, patient_id: str, role: str = "user") -> List[Dict[str, Any]]:
        """Returns all sessions associated with a given patient ID."""
        docs = self.db.query(Document).all()
        matching_doc_ids = [d.id for d in docs if d.meta_data and d.meta_data.get(
            "patient_id") == patient_id]

        if not matching_doc_ids:
            return []

        sessions = self.db.query(PipelineSession).filter(PipelineSession.document_id.in_(
            matching_doc_ids)).order_by(PipelineSession.created_at.desc()).all()

        results = []
        for s in sessions:
            res = self.get_session_results(s.id, role)
            if res:
                doc = next((d for d in docs if d.id == s.document_id), None)
                if doc:
                    res["original_text"] = doc.content
                results.append(res)

        return results

    def log_phi_redaction(self, session_id: str, field_type: str, original_value: str, redacted_value: str) -> PHIAuditLog:
        """Logs a PHI redaction event to the compliance audit database table."""
        audit_id = str(uuid.uuid4())
        audit = PHIAuditLog(
            id=audit_id,
            session_id=session_id,
            field_type=field_type,
            original_value=original_value,
            redacted_value=redacted_value
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        logger.info(
            f"Audited PHI redaction for session {session_id}: type={field_type}")
        return audit
