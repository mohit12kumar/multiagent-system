import re
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel, field_validator

from backend.database.connection import get_db
from backend.database.models import PatientHistory, PipelineSession, ReviewQueue, User, Document, EntityMention
from backend.orchestrator.coordinator import Coordinator
from backend.api.auth import get_current_user
from backend.utils.pdf_generator import generate_clinical_report_pdf

router = APIRouter(prefix="/api/patient", tags=["Patient Portal"])


class ClinicalNoteSubmissionRequest(BaseModel):
    clinical_note: str

    @field_validator("clinical_note", mode="before")
    @classmethod
    def strip_control_characters(cls, v: str) -> str:
        """Remove invalid JSON control characters that cause 422 JSON decode errors."""
        if isinstance(v, str):
            v = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", v)
        return v


@router.post("/submit-note")
def submit_patient_clinical_note(
    req: ClinicalNoteSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if not req.clinical_note.strip():
        raise HTTPException(status_code=422, detail="Clinical note cannot be empty.")

    try:
        coordinator = Coordinator(db)
        user_id = current_user.get("user_id")
        result = coordinator.run_pipeline(document_content=req.clinical_note, user_id=user_id)

        if result.get("status") == "FAILED":
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline failed at stage '{result.get('current_stage', 'unknown')}': {result.get('error_message', 'Unknown error')}"
            )

        # Return a PENDING_REVIEW response — full results only shown after doctor approves
        return {
            "status": "PENDING_REVIEW",
            "session_id": result.get("session_id"),
            "document_id": result.get("document_id"),
            "patient_message": (
                "✅ Your clinical note has been received and processed by our AI pipeline. "
                "It has been sent to your doctor for review. "
                "You will be able to see your full health summary once your doctor approves it."
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")


@router.get("/history")
def get_patient_history(db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("user_id")

    # Strictly filter by the authenticated user's UUID only
    histories = db.query(PatientHistory).filter(
        PatientHistory.user_id == user_id
    ).order_by(PatientHistory.created_at.desc()).all()

    results = []
    for h in histories:
        # Check ReviewQueue to determine approval status for this session
        review_item = db.query(ReviewQueue).filter(
            ReviewQueue.session_id == h.session_id,
            ReviewQueue.entity_mention_id == None,
            ReviewQueue.medication_relation_id == None
        ).first()

        if review_item is None:
            review_status = "APPROVED"  # No session-level review entry means auto-approved
        elif review_item.status == "PENDING":
            review_status = "PENDING_REVIEW"
        elif review_item.status in ("RESOLVED", "APPROVED"):
            review_status = "APPROVED"
        else:
            review_status = "REJECTED"

        # Only expose full summary if doctor has approved
        summary = h.summary_json if review_status == "APPROVED" else None

        results.append({
            "history_id": h.id,
            "session_id": h.session_id,
            "review_status": review_status,
            "summary": summary,
            "created_at": h.created_at.isoformat() + "Z" if h.created_at else None
        })
    return results


@router.get("/summary/{session_id}")
def get_patient_summary(session_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    ph = db.query(PatientHistory).filter(
        PatientHistory.session_id == session_id,
        PatientHistory.user_id == user_id
    ).first()
    if not ph:
        raise HTTPException(status_code=404, detail="Summary not found for your account")
    return {
        "session_id": session_id,
        "patient_summary": ph.summary_json,
        "created_at": ph.created_at.isoformat() + "Z" if ph.created_at else None
    }


from backend.api.auth import get_current_user, get_current_user_with_query_fallback

@router.get("/download-pdf/{session_id}")
def download_patient_pdf(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user_with_query_fallback)
):
    user_id = current_user.get("user_id")
    user_role = current_user.get("role")

    query = db.query(PatientHistory).filter(PatientHistory.session_id == session_id)
    if user_role != "doctor":
        query = query.filter(PatientHistory.user_id == user_id)
    ph = query.first()
    if not ph:
        raise HTTPException(status_code=404, detail="Report not found for your account")

    rq = db.query(ReviewQueue).filter(
        ReviewQueue.session_id == session_id,
        ReviewQueue.entity_mention_id == None,
        ReviewQueue.medication_relation_id == None
    ).first()

    session = db.query(PipelineSession).filter(PipelineSession.id == session_id).first()

    if rq:
        rev_status = "APPROVED" if rq.status in ("RESOLVED", "APPROVED") else ("REJECTED" if rq.status == "REJECTED" else "PENDING_REVIEW")
    else:
        rev_status = "APPROVED" if (session and session.status == "COMPLETED") else "PENDING_REVIEW"

    data = {
        "session_id": session_id,
        "review_status": rev_status,
        "patient_summary": ph.summary_json,
        "doctor_report": "Patient Self-Submitted Clinical Overview"
    }
    pdf_bytes = generate_clinical_report_pdf(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=patient_clinical_report_{session_id}.pdf"}
    )


@router.get("/sessions/user/{patient_id}")
def get_user_sessions_by_id(
    patient_id: str,
    role: str = "user",
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieves all sessions for a given patient ID, merging metadata and raw entities."""
    user_id = current_user.get("user_id")
    user_role = current_user.get("role")
    username = current_user.get("username")

    if user_role != "doctor" and user_id != patient_id and username != patient_id:
        raise HTTPException(
            status_code=403,
            detail="Access forbidden: You can only access your own patient records."
        )
    histories = []
    user = db.query(User).filter(User.username == patient_id).first()
    if user:
        histories = db.query(PatientHistory).filter(PatientHistory.user_id == user.id).all()
    else:
        # Fallback to metadata check
        docs = db.query(Document).all()
        doc_ids = [d.id for d in docs if d.meta_data and d.meta_data.get("patient_id") == patient_id]
        if doc_ids:
            histories = db.query(PatientHistory).filter(PatientHistory.session_id.in_([
                s.id for s in db.query(PipelineSession).filter(PipelineSession.document_id.in_(doc_ids)).all()
            ])).all()

    results = []
    for h in histories:
        session = db.query(PipelineSession).filter(PipelineSession.id == h.session_id).first()
        if not session:
            continue
            
        doc = db.query(Document).filter(Document.id == session.document_id).first()
        original_text = doc.content if doc else ""
        
        mentions = db.query(EntityMention).filter(EntityMention.session_id == session.id).all()
        entities_list = []
        for m in mentions:
            entities_list.append({
                "id": m.id,
                "text": m.text,
                "type": m.type,
                "start_char": m.start_char,
                "end_char": m.end_char,
                "confidence": m.confidence,
                "canonical_name": m.canonical.name if m.canonical else None
            })
            
        session_data = {
            "session_id": session.id,
            "document_id": session.document_id,
            "status": session.status,
            "current_stage": session.current_stage,
            "created_at": session.created_at.isoformat() + "Z" if session.created_at else None,
            "original_text": original_text,
            "entities": entities_list,
        }
        
        if h.summary_json:
            session_data.update(h.summary_json)
            
        results.append(session_data)
        
    return {"sessions": results}
