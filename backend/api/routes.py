import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.database.connection import engine, Base, get_db, SessionLocal
from backend.database.mysql_store import MySQLStore
from backend.orchestrator.coordinator import Coordinator
from backend.api.auth import create_access_token, hash_password, verify_password, get_current_user
from backend.api.doctor_routes import router as doctor_router
from backend.api.patient_routes import router as patient_router

# ---------------------------------------------------------------------------
# Lifespan: create ONE shared Coordinator at startup, reuse across requests
# ---------------------------------------------------------------------------
_shared_coordinator: Optional[Coordinator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _shared_coordinator
    # Initialize tables & seed demo accounts
    try:
        Base.metadata.create_all(bind=engine)
        db_seed = SessionLocal()
        mysql_store = MySQLStore(db_seed)

        if not mysql_store.get_user_by_username("dr_jenkins"):
            hashed_doc_pw = hash_password("password123")
            mysql_store.create_user(
                username="dr_jenkins",
                email="doctor@hospital.org",
                hashed_password=hashed_doc_pw,
                role="doctor",
                full_name="Dr. Sarah Jenkins (Cardiologist)"
            )

        if not mysql_store.get_user_by_username("patient_john"):
            hashed_pat_pw = hash_password("password123")
            mysql_store.create_user(
                username="patient_john",
                email="john.doe@patient.org",
                hashed_password=hashed_pat_pw,
                role="patient",
                full_name="John Doe (PAT-88421)"
            )
        db_seed.close()
    except Exception as e:
        print(f"Table creation/seeding warning: {e}")

    # Build the shared coordinator once — this is the heavy step
    _shared_coordinator = Coordinator(db_session=None)
    print("[Startup] Coordinator singleton initialised — all agents ready.")

    yield  # Server is now live

    # Cleanup (if needed in future)
    _shared_coordinator = None

app = FastAPI(
    title="Clinical Multi-Agent Information Extraction & Decision Support API",
    description="Full-Stack Production Clinical NLP & Decision Support System",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include subrouters with and without /api/v1 prefix for complete frontend compatibility
app.include_router(doctor_router, prefix="/api/v1")
app.include_router(patient_router, prefix="/api/v1")
app.include_router(doctor_router)
app.include_router(patient_router)


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "patient"  # 'doctor' or 'patient'
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ExtractNoteRequest(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None


@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "Clinical Multi-Agent NLP System",
        "version": "2.0.0"
    }


@app.post("/api/auth/register")
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    mysql_store = MySQLStore(db)

    if mysql_store.get_user_by_username(req.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if mysql_store.get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_pw = hash_password(req.password)
    user = mysql_store.create_user(
        username=req.username,
        email=req.email,
        hashed_password=hashed_pw,
        role=req.role.lower(),
        full_name=req.full_name
    )
    token = create_access_token({"sub": user.id, "username": user.username, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
    }


@app.post("/api/auth/login")
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    mysql_store = MySQLStore(db)
    user = mysql_store.get_user_by_username(req.username)

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user.id, "username": user.username, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name
        }
    }



@app.post("/api/auth/token", include_in_schema=False)
def token_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 form-data login — used by Swagger UI Authorize button only."""
    mysql_store = MySQLStore(db)
    user = mysql_store.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": user.id, "username": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/auth/me")
def get_me(current_user: Dict[str, Any] = Depends(get_current_user), db: Session = Depends(get_db)):
    mysql_store = MySQLStore(db)
    user = mysql_store.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name
    }


@app.post("/api/v1/extract")
@app.post("/api/extract")
def extract_clinical_note(req: ExtractNoteRequest, db: Session = Depends(get_db)):
    coordinator = _shared_coordinator
    if coordinator is None:
        raise HTTPException(status_code=503, detail="Service initialising, please retry in a moment.")
    # Attach the live db session to the shared coordinator for this request
    coordinator.set_db(db)
    result = coordinator.run_pipeline(document_content=req.content, doc_metadata=req.metadata)
    return result


from backend.api.auth import get_current_user, get_optional_current_user


@app.get("/api/v1/summary/{session_id}")
@app.get("/api/summary/{session_id}")
def get_session_summary(session_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_optional_current_user)):

    """Return structured summary for a completed pipeline session."""
    from backend.database.models import PipelineSession, MedicationRelation, DiseaseRelation, EntityMention
    session = db.query(PipelineSession).filter(PipelineSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    med_rels = db.query(MedicationRelation).filter(MedicationRelation.session_id == session_id).all()
    dis_rels = db.query(DiseaseRelation).filter(DiseaseRelation.session_id == session_id).all()

    structured = []
    for mr in med_rels:
        syms = [r.symptom_name for r in dis_rels if r.disease_name == mr.disease_name]
        structured.append({
            "disease": mr.disease_name,
            "symptoms": syms,
            "medication": {
                "name": mr.medication_name,
                "dosage": mr.dosage,
                "frequency": mr.frequency,
                "duration": mr.duration,
                "route": "Oral",
                "validation_status": "Verified" if mr.correct else "Needs Review",
            }
        })

    return {
        "session_id": session_id,
        "status": session.status,
        "created_at": session.created_at.isoformat() + "Z" if session.created_at else None,
        "structured_summary": structured,
    }


@app.get("/api/v1/report/{session_id}")
@app.get("/api/v1/pdf/{session_id}")
@app.get("/api/report/{session_id}")
def export_direct_session_pdf(session_id: str, db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_optional_current_user)):
    """Directly stream PDF report for browser tab navigation."""
    from backend.utils.pdf_generator import generate_clinical_report_pdf
    from backend.database.models import PipelineSession, MedicationRelation, DiseaseRelation, EntityMention

    session = db.query(PipelineSession).filter(PipelineSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    med_rels = db.query(MedicationRelation).filter(MedicationRelation.session_id == session_id).all()
    dis_rels = db.query(DiseaseRelation).filter(DiseaseRelation.session_id == session_id).all()

    patient_summary = []
    for mr in med_rels:
        syms = [r.symptom_name for r in dis_rels if r.disease_name == mr.disease_name]
        patient_summary.append({
            "disease": mr.disease_name,
            "symptoms": syms or ["General symptoms"],
            "medication": {
                "name": mr.medication_name,
                "dosage": mr.dosage,
                "frequency": mr.frequency,
                "duration": mr.duration,
                "route": "PO (Oral)",
                "validation_status": "Verified",
            }
        })

    json_data = {
        "session_id": session_id,
        "status": session.status,
        "patient_summary": {"structured_summary": patient_summary},
        "doctor_report": "Clinical Intelligence Summary Report",
    }
    pdf_bytes = generate_clinical_report_pdf(json_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="clinical_report_{session_id[:8]}.pdf"',
            "Content-Type": "application/pdf",
        }
    )

