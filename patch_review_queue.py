"""Patch the doctor_routes.py review-queue endpoint to return ALL items (not just PENDING)."""
import os

src_path = os.path.join(os.path.dirname(__file__), 'backend', 'api', 'doctor_routes.py')
with open(src_path, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

# Find the review-queue GET route (line 77, 0-indexed 76)
start = None
end = None
for i, line in enumerate(lines):
    if '@router.get("/review-queue")' in line:
        start = i
    if start is not None and i > start and line.startswith('@router.') or (start is not None and i > start and 'approve-all' in line):
        end = i
        break

print(f"Found route at lines {start+1}-{end} (0-indexed {start}-{end-1})")

new_block = '''\
@router.get("/review-queue")
def get_doctor_review_queue(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_doctor)
):
    """Return all review queue items. Pass ?status_filter=PENDING to filter."""
    from backend.database.models import ReviewQueue as RQM, PatientHistory as PHM
    q = db.query(RQM)
    if status_filter:
        q = q.filter(RQM.status == status_filter.upper())
    items = q.order_by(RQM.created_at.desc()).all()
    results = []
    for item in items:
        md = None
        if item.entity_mention:
            em = item.entity_mention
            md = {
                "type": "entity_mention",
                "text": em.text,
                "entity_type": em.type,
                "confidence": em.confidence,
                "source_agents": em.source_agents,
            }
        elif item.medication_relation:
            mr = item.medication_relation
            md = {
                "type": "medication_relation",
                "disease": mr.disease_name,
                "medication": mr.medication_name,
                "correct": mr.correct,
                "confidence": mr.confidence,
                "dosage": mr.dosage,
                "frequency": mr.frequency,
                "duration": mr.duration,
                "validation_status": mr.validation_status,
            }
        else:
            sess = item.session
            doc_c = ""
            ps = []
            puid = None
            pname = "Patient"
            if sess:
                if sess.document:
                    doc_c = sess.document.content or ""
                ph = db.query(PHM).filter(PHM.session_id == sess.id).first()
                if ph:
                    ps = ph.summary_json or []
                    puid = ph.user_id
                    if ph.user:
                        pname = ph.user.full_name or ph.user.username
            md = {
                "type": "patient_submission",
                "raw_note": doc_c,
                "patient_user_id": puid,
                "patient_name": pname,
                "patient_summary": ps,
            }
        results.append({
            "id": item.id,
            "session_id": item.session_id,
            "status": item.status,
            "reason": item.reason,
            "created_at": item.created_at.isoformat() + "Z" if item.created_at else None,
            "details": md,
        })
    return results

'''

out = lines[:start] + new_block.split('\n') + lines[end:]
with open(src_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print(f"Done. New file has {len(out)} lines.")
