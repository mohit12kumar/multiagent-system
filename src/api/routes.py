import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.db.models import EntityMention, ReviewQueue, ReviewLog
from src.memory.mysql_store import MySQLStore
from src.memory.chroma_store import ChromaStore
from src.orchestrator.coordinator import Coordinator
from src.monitoring.logger import logger

router = APIRouter()

# Pydantic Schemas for Requests


class ExtractRequest(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None
    role: Optional[str] = "doctor"


class FeedbackRequest(BaseModel):
    entity_mention_id: str
    reviewer: str = "human_reviewer"
    action: str  # APPROVED, REJECTED, MODIFIED
    new_text: Optional[str] = None
    new_type: Optional[str] = None


class BulkFeedbackRequest(BaseModel):
    entity_mention_ids: list[str]
    reviewer: str = "human_reviewer"
    action: str = "APPROVED"


@router.post("/extract")
def extract_entities(request: ExtractRequest, db: Session = Depends(get_db)):
    """
    Submits a text document to run the multi-agent extraction pipeline.
    """
    try:
        coordinator = Coordinator(db)
        if request.metadata is None:
            request.metadata = {}
        request.metadata["role"] = request.role
        results = coordinator.run_pipeline(request.text, request.metadata)
        return results
    except Exception as e:
        logger.error(f"Extraction route failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
def get_session_status(session_id: str, role: str = Query("doctor"), db: Session = Depends(get_db)):
    """
    Retrieves the execution status and extracted entities for a pipeline session.
    """
    store = MySQLStore(db)
    results = store.get_session_results(session_id, role)
    if not results:
        raise HTTPException(
            status_code=404, detail=f"Session {session_id} not found")
    return results


@router.get("/sessions/user/{patient_id}")
def get_user_sessions(patient_id: str, role: str = Query("user"), db: Session = Depends(get_db)):
    """
    Retrieves all sessions for a given patient ID.
    """
    store = MySQLStore(db)
    results = store.get_sessions_by_patient_id(patient_id, role)
    return {"sessions": results}


@router.get("/review/queue")
def get_review_queue(db: Session = Depends(get_db)):
    """
    Lists all entities currently pending human review.
    """
    queue_items = db.query(ReviewQueue).filter(
        ReviewQueue.status == "PENDING").all()

    sessions_map = {}

    for item in queue_items:
        mention = item.entity_mention
        if not mention:
            continue

        session = mention.session
        if not session:
            continue

        document = session.document

        if session.id not in sessions_map:
            sessions_map[session.id] = {
                "session_id": session.id,
                "original_text": document.content if document else "",
                "created_at": session.created_at.isoformat() + "Z" if session.created_at else "",
                "entities": []
            }

        sessions_map[session.id]["entities"].append({
            "queue_id": item.id,
            "entity_mention_id": item.entity_mention_id,
            "text": mention.text,
            "type": mention.type,
            "confidence": mention.confidence,
            "source_agents": mention.source_agents.split(",") if mention.source_agents else [],
            "created_at": item.created_at.isoformat() + "Z" if item.created_at else ""
        })

    return {"pending_sessions": list(sessions_map.values())}


@router.post("/review/feedback")
def submit_review_feedback(feedback: FeedbackRequest, db: Session = Depends(get_db)):
    """
    Receives feedback (e.g. corrections or approvals) on entity mentions,
    updates the record, resolves review queue tasks, and updates the vector search index.
    """
    # 1. Fetch mention and review queue task
    mention = db.query(EntityMention).filter(
        EntityMention.id == feedback.entity_mention_id).first()
    if not mention:
        raise HTTPException(status_code=404, detail="Entity mention not found")

    queue_item = db.query(ReviewQueue).filter(
        ReviewQueue.entity_mention_id == feedback.entity_mention_id,
        ReviewQueue.status == "PENDING"
    ).first()

    store = MySQLStore(db)
    chroma = ChromaStore()

    old_text = mention.text
    old_type = mention.type

    action = feedback.action.upper()

    # 2. Apply corrections based on feedback action
    if action == "APPROVED":
        # Check if this entity name already has a canonical record
        canonical = store.get_canonical_entity_by_name(mention.text)
        if not canonical:
            # Create canonical profile and index it in ChromaDB for future extraction linking!
            canonical = store.create_canonical_entity(
                name=mention.text,
                entity_type=mention.type,
                description=f"Human-approved entity from session {mention.session_id}"
            )
            chroma.add_entity(canonical.id, canonical.name, canonical.type)

        mention.canonical_id = canonical.id
        # Boost confidence to max since it is human verified
        mention.confidence = 1.0

        # Log approval
        log = ReviewLog(
            id=str(uuid.uuid4()),
            entity_mention_id=mention.id,
            reviewer=feedback.reviewer,
            action="APPROVED",
            old_value=old_text,
            new_value=old_text
        )
        db.add(log)
        logger.info(f"Human approved entity '{old_text}'")

    elif action == "MODIFIED":
        new_text = feedback.new_text or old_text
        new_type = feedback.new_type or old_type

        # Update mention values
        mention.text = new_text
        mention.type = new_type
        mention.confidence = 1.0  # Human corrected is absolute

        # Check or create canonical record for the new text
        canonical = store.get_canonical_entity_by_name(new_text)
        if not canonical:
            canonical = store.create_canonical_entity(
                name=new_text,
                entity_type=new_type,
                description=f"Human-corrected entity. Original mention: {old_text}"
            )
            chroma.add_entity(canonical.id, canonical.name, canonical.type)

        mention.canonical_id = canonical.id

        # Log modification
        log = ReviewLog(
            id=str(uuid.uuid4()),
            entity_mention_id=mention.id,
            reviewer=feedback.reviewer,
            action="MODIFIED",
            old_value=f"{old_text} ({old_type})",
            new_value=f"{new_text} ({new_type})"
        )
        db.add(log)
        logger.info(f"Human corrected entity '{old_text}' to '{new_text}'")

    elif action == "REJECTED":
        # Log rejection
        log = ReviewLog(
            id=str(uuid.uuid4()),
            entity_mention_id=mention.id,
            reviewer=feedback.reviewer,
            action="REJECTED",
            old_value=old_text,
            new_value=None
        )
        db.add(log)

        # Delete the mention from current entity mentions table or lower confidence to zero
        db.delete(mention)
        logger.info(f"Human rejected and deleted entity '{old_text}'")
    else:
        raise HTTPException(
            status_code=400, detail="Invalid review action. Use APPROVED, REJECTED, or MODIFIED")

    # 3. Mark queue task as resolved
    if queue_item:
        queue_item.status = "RESOLVED"

    db.commit()
    return {"status": "success", "action": action, "entity_mention_id": feedback.entity_mention_id}


@router.post("/review/feedback/bulk")
def submit_bulk_review_feedback(bulk_feedback: BulkFeedbackRequest, db: Session = Depends(get_db)):
    """
    Applies the same review action (e.g. APPROVED) to multiple entity mentions at once.
    """
    results = []
    for mention_id in bulk_feedback.entity_mention_ids:
        try:
            single_feedback = FeedbackRequest(
                entity_mention_id=mention_id,
                reviewer=bulk_feedback.reviewer,
                action=bulk_feedback.action
            )
            submit_review_feedback(single_feedback, db)
            results.append(
                {"entity_mention_id": mention_id, "status": "success"})
        except Exception as e:
            results.append({"entity_mention_id": mention_id,
                           "status": "failed", "error": str(e)})

    return {"bulk_results": results}
