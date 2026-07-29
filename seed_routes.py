"""Add ReviewQueue startup seeding into routes.py."""
import os

routes_path = os.path.join(os.path.dirname(__file__), 'backend', 'api', 'routes.py')
with open(routes_path, 'r', encoding='utf-8') as f:
    content = f.read()

seed_code = """
        # Seed demo ReviewQueue item if empty
        from backend.database.models import ReviewQueue
        if db_seed.query(ReviewQueue).count() == 0:
            pat = mysql_store.get_user_by_username("patient_john")
            pat_id = pat.id if pat else None
            doc1_id = str(uuid.uuid4())
            sess1_id = str(uuid.uuid4())
            sample_note_1 = (
                "Patient: John Doe, 58-year-old male presenting with acute chest pain, shortness of breath, and dizziness. "
                "BP 160/95, HR 102 bpm, RR 20/min. Labs: Troponin-I 0.12 ng/mL, BNP 320 pg/mL. "
                "ECG: ST elevation in anterolateral leads. "
                "History of Type 2 Diabetes Mellitus and Essential Hypertension. "
                "Medications: Metformin 500mg PO BID, Lisinopril 10mg PO OD. "
                "Impression: Acute STEMI in patient with poorly controlled T2DM and HTN."
            )
            mysql_store.create_document(doc1_id, sample_note_1, {"patient_id": "PAT-88421"}, user_id=pat_id)
            mysql_store.create_session(sess1_id, doc1_id)
            mysql_store.update_session(sess1_id, "COMPLETED", "FINISHED")
            mysql_store.save_patient_history(user_id=pat_id, session_id=sess1_id, summary_json=[
                {
                    "disease": "Acute STEMI",
                    "symptoms": ["chest pain", "shortness of breath", "dizziness"],
                    "medication": {"name": "Metformin", "dosage": "500mg", "frequency": "PO BID", "duration": "Ongoing"}
                },
                {
                    "disease": "Type 2 Diabetes Mellitus",
                    "symptoms": ["elevated HbA1c"],
                    "medication": {"name": "Lisinopril", "dosage": "10mg", "frequency": "PO OD", "duration": "Ongoing"}
                }
            ])
            mysql_store.save_session_review_entry(session_id=sess1_id, user_id=pat_id)
            print("[Startup] Seeded demo ReviewQueue session for patient_john.")
"""

marker = "db_seed.close()"
if "Seeded demo ReviewQueue" not in content and marker in content:
    content = content.replace(marker, seed_code + "\n        " + marker, 1)
    with open(routes_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully patched routes.py with startup demo ReviewQueue seeding.")
else:
    print("Already patched or marker missing.")
